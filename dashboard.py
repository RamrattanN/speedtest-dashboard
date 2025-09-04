#!/usr/bin/env python3
"""
Speedtest dashboard (compact UI + navy accents):
- Settings expander (Timezone, Theme, Color selection)
- Full IANA timezone list, default America/Chicago
- Default chart type = Bar
- Manual refresh button (disabled when auto-refresh is ON), optional 60s auto-refresh
- Robust server filter (handles blank IDs, string-normalizes)
- Dynamic sampling caption
- Window choices: Last Hour, Last 24 hours, Last 7 days, Last 30 days, Last 12 months
- Previous-period overlay aligned to the current window
- User color pickers (defaults: Upload #8BDCCD, Download #1976D2, Ping #20B9D8)
- Force Streamlit UI accents (radios/toggles/checkboxes/select & server tags) to navy #001F54
"""

from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from zoneinfo import ZoneInfo, available_timezones  # pip install tzdata on Windows

# -------- PATHS / CONFIG --------
ROOT = Path(r"C:\Users\niles\Dropbox\Python Code\Speedtest")
DEFAULT_CSV = ROOT / "speedtest_results.csv"
DEFAULT_CSV.parent.mkdir(parents=True, exist_ok=True)

ALL_TZS = sorted(available_timezones())
DEFAULT_TZ = "America/Chicago"

# Default series colors (your preference)
DEFAULT_COLOR_UPLOAD = "#8BDCCD"
DEFAULT_COLOR_DOWNLOAD = "#1976D2"
DEFAULT_COLOR_PING = "#20B9D8"

# Global accent color
ACCENT_NAVY = "#001F54"

# -------- THEME HELPERS --------
def detect_windows_theme() -> str:
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if int(val) == 1 else "dark"
    except Exception:
        return "light"

def apply_theme_css(theme: str) -> str:
    """Apply base colors and force navy accents for Streamlit widgets."""
    if theme == "dark":
        bg, fg = "#0e1117", "#fafafa"
        template = "plotly_dark"
    else:
        bg, fg = "white", "#0e0e0e"
        template = "plotly_white"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {fg};
        }}

        /* Try to set Streamlit's logical 'primary color' via CSS vars */
        :root {{
            --primary-color: {ACCENT_NAVY};
            --accent-color:  {ACCENT_NAVY};
        }}

        /* 1) Radios & checkboxes (native inputs) */
        input[type="radio"], input[type="checkbox"] {{
            accent-color: {ACCENT_NAVY} !important;
        }}

        /* 2) Streamlit's custom checkbox/radio containers (BaseWeb) */
        /* checked circle for radio */
        [role="radiogroup"] [aria-checked="true"] {{
            border-color: {ACCENT_NAVY} !important;
            background-color: {ACCENT_NAVY} !important;
        }}
        /* radio hover/focus ring */
        [role="radiogroup"] > label:hover > div, [role="radiogroup"] > label:focus > div {{
            box-shadow: 0 0 0 1px {ACCENT_NAVY}55;
            border-color: {ACCENT_NAVY}55;
        }}

        /* checkbox tick */
        [role="checkbox"][aria-checked="true"] {{
            background-color: {ACCENT_NAVY} !important;
            border-color: {ACCENT_NAVY} !important;
        }}
        /* checkbox focus ring */
        [role="checkbox"]:focus {{
            box-shadow: 0 0 0 1px {ACCENT_NAVY}55 !important;
            border-color: {ACCENT_NAVY}55 !important;
        }}

        /* 3) Toggle switch */
        [data-testid="stSwitch"] input:checked + div {{
            background-color: {ACCENT_NAVY} !important;
            border-color: {ACCENT_NAVY} !important;
        }}

        /* 4) Select / Multiselect borders & focus ring */
        div[data-baseweb="select"] > div {{
            border-color: {ACCENT_NAVY}33 !important;
        }}
        div[data-baseweb="select"] > div:focus-within {{
            box-shadow: 0 0 0 1px {ACCENT_NAVY} !important;
            border-color: {ACCENT_NAVY} !important;
        }}

        /* 5) Tags (server chips) */
        div[data-baseweb="tag"] {{
            background-color: {ACCENT_NAVY}1F !important; /* ~12% */
            border-color: {ACCENT_NAVY} !important;
            color: {ACCENT_NAVY} !important;
        }}
        div[data-baseweb="tag"] svg path {{
            fill: {ACCENT_NAVY} !important; /* the 'x' icon */
        }}

        /* 6) Buttons */
        .stButton > button {{
            border-color: {ACCENT_NAVY} !important;
            color: {ACCENT_NAVY} !important;
        }}
        .stButton > button:hover {{
            background-color: {ACCENT_NAVY}0F !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return template

# -------- COLOR HELPERS --------
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b)

def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    r, g, b = (int(_clamp01(c) * 255 + 0.5) for c in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"

def _blend(rgb_a: tuple[float, float, float], rgb_b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    t = _clamp01(t)
    return (
        rgb_a[0] * (1 - t) + rgb_b[0] * t,
        rgb_a[1] * (1 - t) + rgb_b[1] * t,
        rgb_a[2] * (1 - t) + rgb_b[2] * t,
    )

def derive_overlay_color(base_hex: str, theme: str) -> str:
    base = _hex_to_rgb(base_hex)
    target = (1.0, 1.0, 1.0) if theme != "dark" else (0.0, 0.0, 0.0)
    overlay = _blend(base, target, 0.25)
    return _rgb_to_hex(overlay)

# -------- DATA HELPERS --------
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name"])
    df = pd.read_csv(path)

    for c in ["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name"]:
        if c not in df.columns:
            df[c] = pd.NA

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    sid = df["server_id"].astype(str)
    sid = sid.replace(to_replace=r"^(nan|NaN|None)$", value="", regex=True)
    sid = sid.str.replace(r"\.0$", "", regex=True).str.strip()
    df["server_id"] = sid

    sname = df["server_name"].astype(str).replace(to_replace=r"^(nan|NaN|None)$", value="", regex=True).str.strip()
    df["server_name"] = sname

    return df

def infer_sample_minutes(df: pd.DataFrame) -> int | None:
    if df.shape[0] < 2:
        return None
    deltas_min = df["timestamp"].diff().dropna().dt.total_seconds() / 60.0
    if deltas_min.empty:
        return None
    lo, hi = np.percentile(deltas_min, [5, 95])
    trimmed = deltas_min[(deltas_min >= lo) & (deltas_min <= hi)]
    if trimmed.empty:
        trimmed = deltas_min
    return int(max(1, min(round(trimmed.median()), 1440)))

def convert_to_tz(utc_series: pd.Series, tz_name: str) -> pd.Series:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return utc_series.dt.tz_convert(tz)

def resample_overlay(df_local: pd.DataFrame, how: str) -> pd.DataFrame:
    return (
        df_local.set_index("timestamp_local")
        .resample(how)
        .agg({"download_mbps": "mean", "upload_mbps": "mean", "ping_ms": "mean"})
        .dropna(how="all")
        .reset_index()
    )

# Window helpers
from datetime import timedelta
def window_delta(choice: str) -> timedelta:
    if choice == "Last Hour":
        return timedelta(hours=1)
    if choice == "Last 24 hours":
        return timedelta(days=1)
    if choice == "Last 7 days":
        return timedelta(days=7)
    if choice == "Last 30 days":
        return timedelta(days=30)
    if choice == "Last 12 months":
        return timedelta(days=365)
    return timedelta(days=30)

def slice_window(df_local: pd.DataFrame, now_local: pd.Timestamp, choice: str) -> pd.DataFrame:
    if choice == "Last Hour":
        return df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(hours=1))]
    if choice == "Last 24 hours":
        return df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=1))]
    if choice == "Last 7 days":
        return df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=7))]
    if choice == "Last 30 days":
        return df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=30))]
    if choice == "Last 12 months":
        return df_local[df_local["timestamp_local"] >= (now_local - pd.Timedelta(days=365))]
    return df_local

def previous_period_overlay(current_window: pd.DataFrame, full_df_local: pd.DataFrame, choice: str) -> pd.DataFrame:
    if current_window.empty:
        return pd.DataFrame(columns=current_window.columns)
    delta = window_delta(choice)
    start = current_window["timestamp_local"].min()
    end = current_window["timestamp_local"].max()
    prev_start = start - delta
    prev_end = end - delta
    prev_slice = full_df_local[
        (full_df_local["timestamp_local"] >= prev_start) & (full_df_local["timestamp_local"] <= prev_end)
    ].copy()
    if prev_slice.empty:
        return prev_slice
    prev_slice["timestamp_local"] = prev_slice["timestamp_local"] + pd.Timedelta(delta)
    return prev_slice

# -------- PAGE --------
st.set_page_config(page_title="Speedtest Monitor", layout="wide")
st.title("Speedtest Monitor")

# Minimal top controls
c1, c2 = st.columns([1, 1])
with c1:
    chart_mode = st.radio("Chart Type", ["Bar", "Line / Curve"], index=0, horizontal=True)
with c2:
    autorefresh = st.toggle("Auto-refresh every 60s", value=True)

refresh_clicked = st.button("Refresh now", disabled=autorefresh, key="refresh_now_btn")

if autorefresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60_000, key="refresh")
    except ImportError:
        st.caption("Auto-refresh helper not installed.  Run: pip install streamlit-autorefresh")
else:
    if refresh_clicked:
        st.rerun()

# SETTINGS
with st.expander("Settings", expanded=False):
    st.markdown("**Settings / Timezone**")
    tz_name = st.selectbox(
        "Timezone", ALL_TZS, index=(ALL_TZS.index(DEFAULT_TZ) if DEFAULT_TZ in ALL_TZS else ALL_TZS.index("UTC"))
    )

    st.markdown("**Settings / Theme**")
    theme_choice = st.selectbox("Theme", ["Auto (Windows)", "Light", "Dark"], index=0)

    st.markdown("**Settings / Color selection**")
    theme = detect_windows_theme() if theme_choice.startswith("Auto") else ("dark" if theme_choice.lower().startswith("dark") else "light")
    plotly_template = apply_theme_css(theme)

    colc1, colc2, colc3 = st.columns(3)
    with colc1:
        color_down = st.color_picker("Download color", DEFAULT_COLOR_DOWNLOAD, key="color_down")
    with colc2:
        color_up   = st.color_picker("Upload color", DEFAULT_COLOR_UPLOAD, key="color_up")
    with colc3:
        color_ping = st.color_picker("Ping color", DEFAULT_COLOR_PING, key="color_ping")

# If expander not opened, still set defaults
if "theme" not in locals():
    theme = detect_windows_theme()
    plotly_template = apply_theme_css(theme)
    color_down, color_up, color_ping = DEFAULT_COLOR_DOWNLOAD, DEFAULT_COLOR_UPLOAD, DEFAULT_COLOR_PING

# Derived overlay colors
overlay_down = derive_overlay_color(color_down, theme)
overlay_up   = derive_overlay_color(color_up, theme)
overlay_ping = derive_overlay_color(color_ping, theme)

# Load data
df = load_data(DEFAULT_CSV)
if df.empty:
    st.caption("Each point represents a sample.  Data retained for 30 days (main CSV).")
    st.info(f"No data yet.  Waiting for collector to write results to:\n{DEFAULT_CSV}")
    st.stop()

# Caption with detected sampling interval
sample_min = infer_sample_minutes(df)
if sample_min is None:
    st.caption("Each point represents a sample.  Data retained for 30 days (main CSV).")
else:
    unit = "minute" if sample_min == 1 else "minutes"
    st.caption(f"Each point represents a {sample_min}-{unit} sample.  Data retained for 30 days (main CSV).")

# Server filter
servers_df = df[["server_id", "server_name"]].copy()
has_id_mask = servers_df["server_id"].astype(str).str.len() > 0
servers_df = servers_df[has_id_mask]
servers_df["label"] = servers_df["server_id"] + " · " + servers_df["server_name"].replace("", "(no name)")
server_labels = sorted(servers_df["label"].unique())

col_srv1, col_srv2 = st.columns([3, 1])
with col_srv1:
    selected_labels = st.multiselect("Servers", server_labels, default=server_labels)
with col_srv2:
    include_blank = st.checkbox("Include blanks", value=True, help="Include rows with no server ID/name")

if selected_labels:
    selected_ids = set(l.split(" · ", 1)[0] for l in selected_labels)
    mask = df["server_id"].isin(selected_ids)
    if include_blank:
        mask = mask | (df["server_id"] == "")
    df = df[mask]
else:
    if not include_blank:
        df = df[df["server_id"] != ""]

# TZ conversion
df_local = df.copy()
df_local["timestamp_local"] = convert_to_tz(df_local["timestamp"], tz_name)

# Window and overlay controls
range_choice = st.selectbox(
    "Show window", ["Last Hour", "Last 24 hours", "Last 7 days", "Last 30 days", "Last 12 months"], index=2
)
show_prev_overlay = st.checkbox(
    "Show previous period overlay",
    value=False,
    help="Compare against the immediately preceding period of the same length.",
)

now_local = datetime.now(ZoneInfo(tz_name))
current_window = slice_window(df_local, now_local, range_choice)
if current_window.empty:
    st.info("No data in the selected window.")
    st.stop()

prev_aligned = pd.DataFrame()
if show_prev_overlay:
    prev_aligned = previous_period_overlay(current_window, df_local, range_choice)

# Chart
fig = go.Figure()
x = current_window["timestamp_local"]

if chart_mode.startswith("Bar"):
    fig.add_bar(
        name="Download (Mbps)",
        x=x,
        y=current_window["download_mbps"],
        marker=dict(color=color_down, line=dict(width=0)),
        opacity=0.85,
        legendgroup="primary_down",
    )
    fig.add_bar(
        name="Upload (Mbps)",
        x=x,
        y=current_window["upload_mbps"],
        marker=dict(color=color_up, line=dict(width=0)),
        opacity=0.85,
        legendgroup="primary_up",
    )
    fig.add_trace(
        go.Scatter(
            name="Ping (ms)",
            x=x,
            y=current_window["ping_ms"],
            mode="lines",
            line=dict(color=color_ping, width=2),
            yaxis="y2",
            legendgroup="primary_ping",
        )
    )
else:
    fig.add_trace(
        go.Scatter(
            name="Download (Mbps)",
            x=x,
            y=current_window["download_mbps"],
            mode="lines",
            line=dict(color=color_down, width=2.5),
            legendgroup="primary_down",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Upload (Mbps)",
            x=x,
            y=current_window["upload_mbps"],
            mode="lines",
            line=dict(color=color_up, width=2.5),
            legendgroup="primary_up",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Ping (ms)",
            x=x,
            y=current_window["ping_ms"],
            mode="lines",
            line=dict(color=color_ping, width=2.5),
            yaxis="y2",
            legendgroup="primary_ping",
        )
    )

# Previous-period overlay
if show_prev_overlay and not prev_aligned.empty:
    x_prev = prev_aligned["timestamp_local"]
    fig.add_trace(
        go.Scatter(
            name="Prev period Download",
            x=x_prev,
            y=prev_aligned["download_mbps"],
            mode="lines",
            line=dict(color=derive_overlay_color(color_down, theme), width=3.0, dash="dash"),
            opacity=0.95,
            legendgroup="overlay_down",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Prev period Upload",
            x=x_prev,
            y=prev_aligned["upload_mbps"],
            mode="lines",
            line=dict(color=derive_overlay_color(color_up, theme), width=3.0, dash="dash"),
            opacity=0.95,
            legendgroup="overlay_up",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Prev period Ping",
            x=x_prev,
            y=prev_aligned["ping_ms"],
            mode="lines",
            line=dict(color=derive_overlay_color(color_ping, theme), width=3.0, dash="dash"),
            opacity=0.95,
            yaxis="y2",
            legendgroup="overlay_ping",
        )
    )

fig.update_layout(
    template=plotly_template,
    barmode="group",
    legend_title_text="Metrics",
    xaxis_title=f"Time ({tz_name})",
    yaxis_title="Speed (Mbps)",
    yaxis2=dict(title="Ping (ms)", overlaying="y", side="right", showgrid=False),
    margin=dict(l=50, r=50, t=50, b=50),
    hovermode="x unified",
)

st.plotly_chart(fig, use_container_width=True)

# Summary
st.subheader("Summary (window above)")
stats = current_window[["download_mbps", "upload_mbps", "ping_ms"]].describe().T[["mean", "min", "max"]]
stats.columns = ["mean", "min", "max"]
st.dataframe(stats, use_container_width=True, height=200)
