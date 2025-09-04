#!/usr/bin/env python3
"""
Interactive web dashboard for Speedtest results (timezone-aware).

Run:
  python -m streamlit run dashboard.py
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone as dt_timezone
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Timezone support
from zoneinfo import ZoneInfo, available_timezones  # Python 3.9+

# ---------- CONFIG ----------
DEFAULT_CSV = Path(r"C:\Users\niles\Dropbox\Python Code\Speedtest\speedtest_results.csv")
DEFAULT_CSV.parent.mkdir(parents=True, exist_ok=True)  # Auto-create folder

# Full list of IANA time zones (type-to-search in Streamlit selectbox)
ALL_TZS = sorted(available_timezones())
DEFAULT_TZ = "America/Chicago"

# ---------- HELPERS ----------
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["timestamp", "ping_ms", "download_mbps", "upload_mbps"])
    df = pd.read_csv(path)
    if df.empty:
        return df
    # Collector writes UTC (either with 'Z' or numeric offset) — parse to UTC-aware
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    return df

def infer_sample_minutes(df: pd.DataFrame) -> int | None:
    """Infer sampling interval (minutes) via median delta between successive UTC timestamps, trimmed for outliers."""
    if df.shape[0] < 2:
        return None
    deltas_min = df["timestamp"].diff().dropna().dt.total_seconds() / 60.0
    if deltas_min.empty:
        return None
    lo, hi = np.percentile(deltas_min, [5, 95])
    trimmed = deltas_min[(deltas_min >= lo) & (deltas_min <= hi)]
    if trimmed.empty:
        trimmed = deltas_min
    minutes = int(round(trimmed.median()))
    return max(1, min(minutes, 1440))

def coerce_zoneinfo(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo("UTC")

def fixed_standard_timezone(tz_name: str) -> dt_timezone:
    """
    Build a fixed-offset tzinfo representing the zone's STANDARD time (no DST).
    We sample a mid-winter date (Jan 15) to capture the standard offset.
    """
    zi = coerce_zoneinfo(tz_name)
    # Choose a recent winter date to avoid historic rule changes
    sample = datetime(2025, 1, 15, 12, 0, 0, tzinfo=zi)
    offset = sample.utcoffset() or timedelta(0)
    return dt_timezone(offset)

def convert_series_to_tz(series_utc: pd.Series, tzinfo_or_zone: object) -> pd.Series:
    """Convert a UTC-aware pandas Series to the provided tzinfo (ZoneInfo or datetime.timezone)."""
    return series_utc.dt.tz_convert(tzinfo_or_zone)

# ---------- PAGE ----------
st.set_page_config(page_title="Speedtest Monitor", layout="wide")
st.title("Speedtest Monitor")

# Controls row
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    chart_mode = st.radio("Chart Type", ["Line / Curve", "Bar"], horizontal=True)
with c2:
    autorefresh = st.toggle("Auto-refresh every 60s", value=True)
with c3:
    # Single dropdown with all time zones, default America/Chicago
    default_index = ALL_TZS.index(DEFAULT_TZ) if DEFAULT_TZ in ALL_TZS else ALL_TZS.index("UTC")
    tz_name = st.selectbox("Timezone", ALL_TZS, index=default_index)
    # Daylight Savings toggle
    use_dst = st.checkbox("Enable Daylight Savings", value=True)

# Always render the manual refresh button; disable when auto-refresh is ON
refresh_clicked = st.button("Refresh now", disabled=autorefresh, key="refresh_now_btn")

# Auto-refresh (optional helper)
if autorefresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60_000, key="refresh")
    except ImportError:
        st.caption("Auto-refresh helper not installed.  Run: pip install streamlit-autorefresh")
else:
    if refresh_clicked:
        st.rerun()

# ---------- LOAD DATA ----------
df = load_data(DEFAULT_CSV)

if df.empty:
    st.caption("Each point represents a sample.  Data retained for 30 days.")
    st.info(f"No data yet.  Waiting for collector to write results to:\n{DEFAULT_CSV}")
    st.stop()

# Dynamic sampling caption (computed in UTC)
sample_min = infer_sample_minutes(df)
if sample_min is None:
    st.caption("Each point represents a sample.  Data retained for 30 days.")
else:
    unit = "minute" if sample_min == 1 else "minutes"
    st.caption(f"Each point represents a {sample_min}-{unit} sample.  Data retained for 30 days.")

# Determine the display timezone according to DST toggle
if use_dst:
    display_tz = coerce_zoneinfo(tz_name)               # full IANA zone (DST-aware)
else:
    display_tz = fixed_standard_timezone(tz_name)       # fixed standard offset (no DST)

# Convert timestamps to the chosen zone for display and filtering
df_local = df.copy()
df_local["timestamp_local"] = convert_series_to_tz(df["timestamp"], display_tz)

# ---------- TIME WINDOW (filter in the chosen zone) ----------
range_choice = st.selectbox("Show window", ["Last 24 hours", "Last 7 days", "Last 30 days", "All data"], index=2)
now_local = datetime.now(display_tz)
if range_choice == "Last 24 hours":
    df_local = df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=1))]
elif range_choice == "Last 7 days":
    df_local = df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=7))]
elif range_choice == "Last 30 days":
    df_local = df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=30))]

if df_local.empty:
    st.info("No data in the selected window.")
    st.stop()

# ---------- PLOT ----------
fig = go.Figure()
x = df_local["timestamp_local"]

if chart_mode == "Bar":
    fig.add_bar(name="Download (Mbps)", x=x, y=df_local["download_mbps"])
    fig.add_bar(name="Upload (Mbps)", x=x, y=df_local["upload_mbps"])
    fig.add_trace(go.Scatter(name="Ping (ms)", x=x, y=df_local["ping_ms"], mode="lines", yaxis="y2"))
else:
    fig.add_trace(go.Scatter(name="Download (Mbps)", x=x, y=df_local["download_mbps"], mode="lines"))
    fig.add_trace(go.Scatter(name="Upload (Mbps)", x=x, y=df_local["upload_mbps"], mode="lines"))
    fig.add_trace(go.Scatter(name="Ping (ms)", x=x, y=df_local["ping_ms"], mode="lines", yaxis="y2"))

fig.update_layout(
    barmode="group",
    legend_title_text="Metrics",
    xaxis_title=f"Time ({tz_name}{'' if use_dst else ' – Standard Time'})",
    yaxis_title="Speed (Mbps)",
    yaxis2=dict(
        title="Ping (ms)",
        overlaying="y",
        side="right",
        showgrid=False,
    ),
    margin=dict(l=50, r=50, t=50, b=50),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

# ---------- SUMMARY ----------
st.subheader("Summary (window above)")
stats = df_local[["download_mbps", "upload_mbps", "ping_ms"]].describe().T[["mean", "min", "max"]]
stats.columns = ["mean", "min", "max"]
st.dataframe(stats, use_container_width=True, height=200)
