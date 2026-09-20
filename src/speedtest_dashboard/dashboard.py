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

from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from zoneinfo import ZoneInfo, available_timezones  # pip install tzdata on Windows

from speedtest_dashboard.app_config import configure_data_paths

# -------- PATHS / CONFIG --------
DEFAULT_CSV, _ARCHIVE_DIR = configure_data_paths()

ALL_TZS = sorted(available_timezones())
DEFAULT_TZ = "America/Chicago"

# Default series colors (your preference)
DEFAULT_COLOR_UPLOAD = "#8BDCCD"
DEFAULT_COLOR_DOWNLOAD = "#1976D2"
DEFAULT_COLOR_PING = "#20B9D8"

# Global accent color
ACCENT_NAVY = "#001F54"

LOGO_B64_PATH = Path(__file__).parent / "assets" / "ramrattan-logo.png.b64"
RAMRATTAN_LOGO_URI = (
    "data:image/png;base64,"
    + "".join(LOGO_B64_PATH.read_text(encoding="utf-8").split())
)

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
        surface, muted, line = "#16202a", "#b8c3cc", "#334454"
        template = "plotly_dark"
    else:
        bg, fg = "#f3f7fa", "#17232e"
        surface, muted, line = "#ffffff", "#5e6c78", "#d6e0e8"
        template = "plotly_white"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {fg};
        }}

        [data-testid="stMainBlockContainer"] {{
            max-width: 1180px;
            padding-top: 1.35rem;
            padding-bottom: 3rem;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        .rr-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 0.8rem;
            padding: 26px 30px;
            border-radius: 20px;
            color: #ffffff;
            background: linear-gradient(135deg, #0d2942, #173f63);
            box-shadow: 0 18px 44px rgba(13, 41, 66, 0.18);
        }}

        .rr-hero-main {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .rr-logo {{
            display: block;
            width: auto;
            height: 78px;
            object-fit: contain;
            flex: 0 0 auto;
        }}

        .rr-hero .eyebrow {{
            margin: 0 0 4px;
            color: #9fc8e8;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.12em;
        }}

        .rr-hero h1 {{
            margin: 0;
            color: #ffffff;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            line-height: 1.08;
        }}

        .rr-hero p:last-child {{
            margin: 7px 0 0;
            color: #d9e8f3;
        }}

        .rr-status {{
            padding: 8px 12px;
            border: 1px solid rgba(255, 255, 255, 0.42);
            border-radius: 999px;
            color: #eaf3fa;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            white-space: nowrap;
        }}

        .rr-section-heading {{
            margin: 0.35rem 0 0.65rem;
        }}

        .rr-section-heading .eyebrow {{
            margin: 0 0 4px;
            color: #2f78b8;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.1em;
        }}

        .rr-section-heading h2 {{
            margin: 0;
            color: {fg};
            font-size: 1.45rem;
        }}

        .rr-section-heading p {{
            margin: 5px 0 0;
            color: {muted};
        }}

        div[data-testid="stMetric"] {{
            min-height: 126px;
            padding: 18px 20px;
            border: 1px solid {line};
            border-radius: 16px;
            background: {surface};
            box-shadow: 0 8px 24px rgba(13, 41, 66, 0.07);
        }}

        div[data-testid="stMetricLabel"] {{
            color: {muted};
            font-weight: 700;
        }}

        div[data-testid="stMetricValue"] {{
            color: {fg};
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: {line};
            border-radius: 18px;
            background: {surface};
            box-shadow: 0 8px 24px rgba(13, 41, 66, 0.06);
        }}

        .rr-help-card {{
            height: 100%;
            padding: 22px 24px;
            border: 1px solid {line};
            border-radius: 16px;
            background: {surface};
            box-shadow: 0 8px 24px rgba(13, 41, 66, 0.06);
        }}

        .rr-help-card h3 {{
            margin: 0 0 10px;
            color: {fg};
        }}

        .rr-help-card p,
        .rr-help-card li {{
            color: {muted};
            line-height: 1.55;
        }}

        .rr-help-card .remember {{
            margin-top: 14px;
            padding: 12px 14px;
            border-left: 4px solid #2f78b8;
            border-radius: 8px;
            background: #eaf3fa;
            color: #173f63;
        }}

        div[data-testid="stDialog"] div[role="dialog"] {{
            position: fixed;
            inset: 0 0 0 auto;
            width: min(500px, 94vw);
            max-width: 500px;
            height: 100vh;
            max-height: 100vh;
            margin: 0;
            border-radius: 22px 0 0 22px;
            border: 0;
            background: {surface};
            box-shadow: -20px 0 60px rgba(13, 41, 66, 0.22);
        }}

        div[data-testid="stDialog"] div[role="dialog"] > div {{
            max-height: 100vh;
            overflow-y: auto;
            padding: 1.15rem 1.35rem 2rem;
        }}

        div[data-testid="stDialog"] .rr-help-card {{
            margin-bottom: 14px;
            padding: 18px 20px;
            box-shadow: none;
        }}

        @media (max-width: 760px) {{
            .rr-hero {{
                align-items: flex-start;
                padding: 22px;
            }}
            .rr-status {{
                display: none;
            }}
            .rr-logo {{
                height: 62px;
            }}
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
st.set_page_config(
    page_title="Ramrattan Speedtest Monitor",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply the shared shell immediately.  The selected chart theme can override it below.
apply_theme_css("light")

st.markdown(
    f"""
    <header class="rr-hero">
      <div class="rr-hero-main">
        <img class="rr-logo" src="{RAMRATTAN_LOGO_URI}" alt="Ramrattan logo">
        <div>
          <p class="eyebrow">RAMRATTAN NETWORK TOOLS</p>
          <h1>Speedtest Monitor</h1>
          <p>Clear, local visibility into connection speed, responsiveness, and reliability.</p>
        </div>
      </div>
      <div class="rr-status">LOCAL MONITOR</div>
    </header>
    """,
    unsafe_allow_html=True,
)


@st.dialog("Help with Speedtest Monitor", width="large")
def render_help_panel() -> None:
    """Render speed-test guidance in a right-side Help panel."""
    st.markdown(
        """
        <div class="rr-section-heading">
          <p class="eyebrow">HELP WITH THIS PAGE</p>
          <h2>Using the Speedtest Monitor</h2>
          <p>Keep this guidance open while reviewing the dashboard.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="rr-help-card">
          <h3>Start and stop the monitor</h3>
          <p><strong>What to do</strong></p>
          <ol>
            <li>Open Terminal in the project folder.</li>
            <li>Run the launcher shown below.</li>
            <li>Keep Terminal open while collecting results.</li>
            <li>Press Control-C in Terminal to stop both processes safely.</li>
          </ol>
          <p class="remember"><strong>Remember:</strong> The collector normally records a result every five minutes.  The dashboard checks for new results every 60 seconds.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.code("./RunSpeedTest.command --interval 300", language="bash")

    st.markdown(
        f"""
        <section class="rr-help-card">
          <h3>Use the dashboard</h3>
          <ol>
            <li>Review the latest-result cards for a quick status check.</li>
            <li>Choose Bar or Line / Curve for the chart style.</li>
            <li>Use View options to select servers, the time window, and comparison overlay.</li>
            <li>Leave Refresh display every 60s enabled to see new CSV results automatically.</li>
            <li>Open Display settings to change timezone, theme, and chart colours.</li>
          </ol>
          <p class="remember"><strong>Data location:</strong> {DEFAULT_CSV}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="rr-help-card">
          <h3>Understand the measurements</h3>
          <ul>
            <li><strong>Download</strong> measures how quickly data reaches this computer.  Higher is generally better.</li>
            <li><strong>Upload</strong> measures how quickly data leaves this computer.  Higher is generally better.</li>
            <li><strong>Ping</strong> measures response time in milliseconds.  Lower is generally better.</li>
            <li><strong>Server</strong> identifies the test location selected for that sample.  Different servers can produce different results.</li>
          </ul>
          <p class="remember"><strong>Remember:</strong> Trends across several samples are more useful than one isolated result.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <section class="rr-help-card">
          <h3>Resolve common issues</h3>
          <ul>
            <li><strong>No data yet:</strong> Confirm the collector is running and wait for its first completed test.</li>
            <li><strong>Dashboard does not update:</strong> Confirm automatic display refresh is enabled, then use Refresh now once if needed.</li>
            <li><strong>Ookla warning:</strong> The monitor can fall back automatically to the Python speed-test engine.</li>
            <li><strong>Port already in use:</strong> Open the Local URL printed most recently in Terminal.</li>
            <li><strong>Need to restart:</strong> Stop with Control-C, pull the latest branch, then run the launcher again.</li>
          </ul>
          <p class="remember"><strong>Remember:</strong> Do not close Terminal if you want collection to continue.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**Ramrattan Speedtest Monitor**")
    st.caption(
        "Built and maintained by Ramrattan.com.  "
        "Data remains on the computer running the monitor."
    )


help_space, help_action = st.columns([6.6, 1.4])
with help_action:
    if st.button(
        "Help with this page",
        key="open_help_panel",
        width="stretch",
    ):
        render_help_panel()


st.markdown(
    """
    <div class="rr-section-heading">
      <p class="eyebrow">CONNECTION OVERVIEW</p>
      <h2>Internet performance at a glance</h2>
      <p>Latest measurements first, with detailed trends and view controls below.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    control_chart, control_refresh, control_manual = st.columns([1.8, 1.35, 1], gap="large")
    with control_chart:
        chart_mode = st.radio(
            "Chart type",
            ["Bar", "Line / Curve"],
            index=0,
            horizontal=True,
        )
    with control_refresh:
        autorefresh = st.toggle("Refresh display every 60s", value=True)
    with control_manual:
        st.write("")
        st.button(
            "Refresh now",
            disabled=autorefresh,
            key="refresh_now_btn",
            width="stretch",
        )

with st.expander("Display settings", expanded=False):
    setting_timezone, setting_theme = st.columns(2, gap="large")
    with setting_timezone:
        tz_name = st.selectbox(
            "Timezone",
            ALL_TZS,
            index=(
                ALL_TZS.index(DEFAULT_TZ)
                if DEFAULT_TZ in ALL_TZS
                else ALL_TZS.index("UTC")
            ),
        )
    with setting_theme:
        theme_choice = st.selectbox(
            "Theme",
            ["Auto (Windows)", "Light", "Dark"],
            index=0,
        )

    theme = (
        detect_windows_theme()
        if theme_choice.startswith("Auto")
        else ("dark" if theme_choice.lower().startswith("dark") else "light")
    )
    plotly_template = apply_theme_css(theme)

    st.markdown("**Chart colours**")
    colc1, colc2, colc3 = st.columns(3)
    with colc1:
        color_down = st.color_picker(
            "Download",
            DEFAULT_COLOR_DOWNLOAD,
            key="color_down",
        )
    with colc2:
        color_up = st.color_picker(
            "Upload",
            DEFAULT_COLOR_UPLOAD,
            key="color_up",
        )
    with colc3:
        color_ping = st.color_picker(
            "Ping",
            DEFAULT_COLOR_PING,
            key="color_ping",
        )


@st.fragment(
    run_every="60s" if autorefresh else None,
    key="dashboard_data",
)
def render_dashboard() -> None:
    """Read and redraw the recorded measurements."""
    df = load_data(DEFAULT_CSV)
    if df.empty:
        with st.container(border=True):
            st.info(f"No data yet.  Waiting for the collector to write results to:\n{DEFAULT_CSV}")
            st.caption("The first completed speed test will appear here automatically.")
        st.stop()

    latest = df.iloc[-1]
    latest_local = latest["timestamp"].tz_convert(ZoneInfo(tz_name))
    latest_server = latest["server_name"] or "Server name unavailable"
    if latest["server_id"]:
        latest_server = f'{latest["server_id"]} · {latest_server}'
    latest_time_text = latest_local.strftime("%I:%M %p").lstrip("0")
    latest_date_text = latest_local.strftime("%b %d, %Y").replace(" 0", " ")

    st.markdown(
        """
        <div class="rr-section-heading">
          <p class="eyebrow">LATEST RESULT</p>
          <h2>Most recent connection check</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_down, metric_up, metric_ping, metric_time = st.columns(4, gap="medium")
    metric_down.metric("Download", f'{latest["download_mbps"]:.1f} Mbps')
    metric_up.metric("Upload", f'{latest["upload_mbps"]:.1f} Mbps')
    metric_ping.metric("Ping", f'{latest["ping_ms"]:.1f} ms')
    metric_time.metric("Recorded", latest_time_text)
    st.caption(
        f"{latest_date_text} · {latest_server} · "
        f'Display timezone: {tz_name}'
    )

    sample_min = infer_sample_minutes(df)
    if sample_min is None:
        sample_caption = "Sampling interval will appear after a second result."
    else:
        unit = "minute" if sample_min == 1 else "minutes"
        sample_caption = f"Observed interval between recorded samples: {sample_min} {unit}."

    servers_df = df[["server_id", "server_name"]].copy()
    has_id_mask = servers_df["server_id"].astype(str).str.len() > 0
    servers_df = servers_df[has_id_mask]
    servers_df["label"] = (
        servers_df["server_id"]
        + " · "
        + servers_df["server_name"].replace("", "(no name)")
    )
    server_labels = sorted(servers_df["label"].unique())

    selected_key = "dashboard_selected_servers"
    known_key = "dashboard_known_servers"
    known_labels = set(st.session_state.get(known_key, []))
    new_labels = set(server_labels) - known_labels
    if selected_key not in st.session_state:
        st.session_state[selected_key] = server_labels
    else:
        still_available = [
            label
            for label in st.session_state[selected_key]
            if label in server_labels
        ]
        st.session_state[selected_key] = still_available + sorted(new_labels)
    st.session_state[known_key] = server_labels

    with st.expander("View options", expanded=True):
        filter_servers, filter_window = st.columns([2.25, 1], gap="large")
        with filter_servers:
            selected_labels = st.multiselect(
                "Servers",
                server_labels,
                key=selected_key,
            )
        with filter_window:
            range_choice = st.selectbox(
                "Show window",
                [
                    "Last Hour",
                    "Last 24 hours",
                    "Last 7 days",
                    "Last 30 days",
                    "Last 12 months",
                ],
                index=2,
            )

        option_blank, option_overlay = st.columns(2)
        with option_blank:
            include_blank = st.checkbox(
                "Include results without a server ID",
                value=True,
                help="Include rows with no server ID or server name.",
            )
        with option_overlay:
            show_prev_overlay = st.checkbox(
                "Show previous period",
                value=False,
                help="Compare against the immediately preceding period of the same length.",
            )
        st.caption(f"{sample_caption}  Data retained for 30 days in the main CSV.")

    if selected_labels:
        selected_ids = {label.split(" · ", 1)[0] for label in selected_labels}
        mask = df["server_id"].isin(selected_ids)
        if include_blank:
            mask = mask | (df["server_id"] == "")
        df = df[mask]
    elif not include_blank:
        df = df[df["server_id"] != ""]

    df_local = df.copy()
    df_local["timestamp_local"] = convert_to_tz(df_local["timestamp"], tz_name)

    now_local = datetime.now(ZoneInfo(tz_name))
    current_window = slice_window(df_local, now_local, range_choice)
    if current_window.empty:
        st.info("No data is available in the selected window.")
        st.stop()

    prev_aligned = pd.DataFrame()
    if show_prev_overlay:
        prev_aligned = previous_period_overlay(
            current_window,
            df_local,
            range_choice,
        )

    fig = go.Figure()
    x = current_window["timestamp_local"]

    if chart_mode.startswith("Bar"):
        fig.add_bar(
            name="Download (Mbps)",
            x=x,
            y=current_window["download_mbps"],
            marker=dict(color=color_down, line=dict(width=0)),
            opacity=0.88,
            legendgroup="primary_down",
        )
        fig.add_bar(
            name="Upload (Mbps)",
            x=x,
            y=current_window["upload_mbps"],
            marker=dict(color=color_up, line=dict(width=0)),
            opacity=0.88,
            legendgroup="primary_up",
        )
        fig.add_trace(
            go.Scatter(
                name="Ping (ms)",
                x=x,
                y=current_window["ping_ms"],
                mode="lines+markers",
                line=dict(color=color_ping, width=2.5),
                marker=dict(size=6),
                yaxis="y2",
                legendgroup="primary_ping",
            )
        )
    else:
        for name, column, color, axis in [
            ("Download (Mbps)", "download_mbps", color_down, "y"),
            ("Upload (Mbps)", "upload_mbps", color_up, "y"),
            ("Ping (ms)", "ping_ms", color_ping, "y2"),
        ]:
            fig.add_trace(
                go.Scatter(
                    name=name,
                    x=x,
                    y=current_window[column],
                    mode="lines+markers",
                    line=dict(color=color, width=2.5, shape="spline"),
                    marker=dict(size=6),
                    yaxis=axis,
                )
            )

    if show_prev_overlay and not prev_aligned.empty:
        x_prev = prev_aligned["timestamp_local"]
        for name, column, color, axis in [
            ("Previous Download", "download_mbps", derive_overlay_color(color_down, theme), "y"),
            ("Previous Upload", "upload_mbps", derive_overlay_color(color_up, theme), "y"),
            ("Previous Ping", "ping_ms", derive_overlay_color(color_ping, theme), "y2"),
        ]:
            fig.add_trace(
                go.Scatter(
                    name=name,
                    x=x_prev,
                    y=prev_aligned[column],
                    mode="lines",
                    line=dict(color=color, width=2.5, dash="dash"),
                    opacity=0.9,
                    yaxis=axis,
                )
            )

    fig.update_layout(
        template=plotly_template,
        height=430,
        barmode="group",
        legend_title_text="Metrics",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        xaxis_title=f"Time ({tz_name})",
        yaxis_title="Speed (Mbps)",
        yaxis2=dict(
            title="Ping (ms)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        margin=dict(l=40, r=40, t=70, b=45),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.markdown(
        """
        <div class="rr-section-heading">
          <p class="eyebrow">PERFORMANCE TREND</p>
          <h2>Recorded speed and responsiveness</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")

    stats = (
        current_window[["download_mbps", "upload_mbps", "ping_ms"]]
        .describe()
        .T[["mean", "min", "max"]]
        .round(2)
    )
    stats.index = ["Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]
    stats.columns = ["Average", "Minimum", "Maximum"]

    st.markdown(
        """
        <div class="rr-section-heading">
          <p class="eyebrow">WINDOW SUMMARY</p>
          <h2>Average and range</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.dataframe(stats, width="stretch", height=180)
        st.caption(
            f"{len(current_window)} recorded "
            f"{'sample' if len(current_window) == 1 else 'samples'} in this view."
        )


render_dashboard()

st.caption(
    "Ramrattan Speedtest Monitor · Local data only · "
    "Use Help for operating guidance and troubleshooting."
)

