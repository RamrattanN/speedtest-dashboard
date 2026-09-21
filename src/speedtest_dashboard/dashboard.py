#!/usr/bin/env python3
"""
Speedtest dashboard (compact UI + navy accents):
- Settings expander (Timezone, Theme, Color selection)
- Full IANA timezone list, default America/Chicago
- Default chart type = Bar
- Manual refresh button when optional 60s auto-refresh is disabled
- Robust server filter (handles blank IDs, string-normalizes)
- Dynamic sampling caption
- Window choices: Last Hour, Last 24 hours, Last 7 days, Last 30 days, Last 12 months
- Previous-period overlay aligned to the current window
- User color pickers (defaults: Upload #8BDCCD, Download #1976D2, Ping #20B9D8)
- Force Streamlit UI accents (radios/toggles/checkboxes/select & server tags) to navy #001F54
"""

import base64
from datetime import datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
import streamlit as st
from zoneinfo import ZoneInfo, available_timezones  # pip install tzdata on Windows

from speedtest_dashboard import __version__
from speedtest_dashboard.app_config import (
    configure_data_paths,
    load_settings,
    set_measurement_engine,
    set_server_preference,
)
from speedtest_dashboard.collector import OOKLA_DOWNLOAD_URL, find_ookla_cli

# -------- PATHS / CONFIG --------
DEFAULT_CSV, _ARCHIVE_DIR = configure_data_paths()

ALL_TZS = sorted(available_timezones())
DEFAULT_TZ = "America/Chicago"

# Default series colors (your preference)
DEFAULT_COLOR_UPLOAD = "#8BDCCD"
DEFAULT_COLOR_DOWNLOAD = "#1976D2"
DEFAULT_COLOR_PING = "#20B9D8"

# Global accent color
ACCENT_NAVY = "#173F63"
DESKTOP_MODE = os.environ.get("SPEEDTEST_DASHBOARD_DESKTOP") == "1"
DESKTOP_PLATFORM = os.environ.get("SPEEDTEST_DASHBOARD_DESKTOP_PLATFORM", "macos")

LOGO_B64_PATH = Path(__file__).parent / "assets" / "ramrattan-logo.png.b64"
RAMRATTAN_LOGO_B64 = "".join(LOGO_B64_PATH.read_text(encoding="utf-8").split())
RAMRATTAN_LOGO_URI = "data:image/png;base64," + RAMRATTAN_LOGO_B64
RAMRATTAN_FAVICON = Image.open(BytesIO(base64.b64decode(RAMRATTAN_LOGO_B64)))

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

        .st-key-hero {{
            margin-bottom: 0.8rem;
            padding: 26px 30px;
            border-radius: 20px;
            color: #ffffff;
            background: linear-gradient(135deg, #0d2942, #173f63);
            box-shadow: 0 18px 44px rgba(13, 41, 66, 0.18);
        }}

        .st-key-hero [data-testid="stHorizontalBlock"] {{
            align-items: center;
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

        .st-key-hero .eyebrow {{
            margin: 0 0 4px;
            color: #9fc8e8;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.12em;
        }}

        .st-key-hero h1 {{
            margin: 0;
            color: #ffffff;
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            line-height: 1.08;
        }}

        .st-key-hero .rr-hero-copy p:last-child {{
            margin: 7px 0 0;
            color: #d9e8f3;
        }}

        .st-key-open_help_panel {{
            display: flex;
            justify-content: flex-end;
        }}

        .st-key-open_help_panel .stButton > button {{
            width: 46px !important;
            min-width: 46px !important;
            height: 46px !important;
            padding: 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.72) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }}

        .st-key-open_help_panel .stButton > button:hover,
        .st-key-open_help_panel .stButton > button:focus-visible {{
            border-color: #ffffff !important;
            background: rgba(255, 255, 255, 0.18) !important;
        }}

        .st-key-open_help_panel .stButton > button p {{
            display: none;
        }}

        .st-key-refresh_now_btn .stButton > button {{
            border-color: #173f63 !important;
            color: #ffffff !important;
            background: #173f63 !important;
        }}

        .st-key-refresh_now_btn .stButton > button:hover,
        .st-key-refresh_now_btn .stButton > button:focus-visible {{
            border-color: #2f78b8 !important;
            background: #2f78b8 !important;
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

        .rr-subsection-heading {{
            margin-top: 1rem;
        }}

        .rr-subsection-heading h3 {{
            margin: 0;
            color: {fg};
            font-size: 1.08rem;
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

        .st-key-help_panel {{
            position: fixed;
            inset: 0 0 0 auto !important;
            z-index: 999999;
            width: min(430px, 96vw) !important;
            max-width: 430px !important;
            height: 100vh;
            max-height: 100vh;
            padding: 18px 20px 30px;
            overflow-y: auto;
            border: 0 !important;
            border-left: 1px solid {line} !important;
            border-radius: 0 !important;
            background: {surface};
            box-shadow: -20px 0 60px rgba(13, 41, 66, 0.22);
        }}

        .st-key-help_panel > div {{
            width: 100%;
        }}

        .st-key-help_panel .rr-help-card {{
            margin-bottom: 14px;
            padding: 18px 20px;
            box-shadow: none;
        }}

        .st-key-help_panel .rr-section-heading {{
            margin-top: 0;
        }}

        button[kind="primary"],
        .stButton > button[kind="primary"] {{
            border-color: #173f63 !important;
            color: #ffffff !important;
            background: #173f63 !important;
        }}

        button[kind="primary"]:hover,
        button[kind="primary"]:focus-visible,
        .stButton > button[kind="primary"]:hover,
        .stButton > button[kind="primary"]:focus-visible {{
            border-color: #2f78b8 !important;
            background: #2f78b8 !important;
        }}

        [data-testid="stSwitch"] [role="switch"][aria-checked="true"],
        [data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"],
        label[data-baseweb="checkbox"]:has(input:checked) > div {{
            border-color: #173f63 !important;
            background-color: #173f63 !important;
        }}

        [data-testid="stRadio"] [role="radio"][aria-checked="true"] > div:first-child,
        [data-testid="stRadio"] input:checked + div {{
            border-color: #173f63 !important;
            background-color: #173f63 !important;
        }}

        [data-testid="stSlider"] [role="slider"] {{
            border-color: #173f63 !important;
            background-color: #173f63 !important;
        }}

        [data-baseweb="tag"],
        [data-baseweb="tag"] span {{
            border-color: #2f78b8 !important;
            color: #173f63 !important;
            background-color: #eaf3fa !important;
        }}

        [data-baseweb="tag"] svg path {{
            fill: #173f63 !important;
        }}

        @media (max-width: 760px) {{
            .st-key-hero {{
                padding: 22px;
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

        /* Keyed controls need final, high-specificity rules because the key class
           and Streamlit button wrapper are the same element in current releases. */
        .st-key-open_help_panel button {{
            width: 46px !important;
            min-width: 46px !important;
            height: 46px !important;
            padding: 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.72) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }}

        .st-key-open_help_panel button:hover,
        .st-key-open_help_panel button:focus-visible {{
            border-color: #ffffff !important;
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.18) !important;
        }}

        .st-key-open_help_panel button [data-testid="stMarkdownContainer"],
        .st-key-open_help_panel button p {{
            display: none !important;
        }}

        .st-key-open_help_panel button [data-testid="stIconMaterial"] {{
            display: inline-flex !important;
            color: #ffffff !important;
            font-size: 1.45rem !important;
        }}

        .st-key-refresh_now_btn button {{
            border-color: #173f63 !important;
            color: #ffffff !important;
            background: #173f63 !important;
        }}

        .st-key-refresh_now_btn button:hover,
        .st-key-refresh_now_btn button:focus-visible {{
            border-color: #2f78b8 !important;
            color: #ffffff !important;
            background: #2f78b8 !important;
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
        return pd.DataFrame(columns=["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name", "engine"])
    df = pd.read_csv(path)

    for c in ["timestamp", "ping_ms", "download_mbps", "upload_mbps", "server_id", "server_name", "engine"]:
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

    engine = df["engine"].astype(str).replace(
        to_replace=r"^(nan|NaN|None)$",
        value="",
        regex=True,
    ).str.strip()
    df["engine"] = engine.replace("", "unknown")

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
    page_icon=RAMRATTAN_FAVICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply the shared shell immediately.  The selected chart theme can override it below.
apply_theme_css("light")

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

    if DESKTOP_MODE:
        if DESKTOP_PLATFORM == "windows":
            launch_location = "the Windows Start menu"
            install_steps = "".join(
                [
                    "<li>Quit any running copy of Speedtest Monitor.</li>",
                    "<li>Run the current Windows x64 installer.</li>",
                    "<li>If an existing installation is detected, choose Repair to install the current application files.</li>",
                    "<li>If Microsoft Defender SmartScreen appears, select More info, then Run anyway.</li>",
                    "<li>Open Speedtest Monitor from the Start menu after installation.</li>",
                    f'<li>Install the official Speedtest CLI from <a href="{OOKLA_DOWNLOAD_URL}" target="_blank">Ookla</a>, then confirm detection under Connection Overview &gt; Measurement engine.</li>',
                    f"<li>Confirm that the controller shows version {__version__}.</li>",
                ]
            )
            security_note = (
                "The Windows release is not code-signed.  The first installer launch "
                "may require explicit SmartScreen approval."
            )
        else:
            launch_location = "the Applications folder"
            install_steps = "".join(
                [
                    "<li>Quit any running copy of Speedtest Monitor.</li>",
                    "<li>Open the current disk image and drag Speedtest Monitor to Applications.</li>",
                    "<li>Choose Replace if macOS reports that an older copy is installed.</li>",
                    "<li>If macOS blocks the unsigned application, select Done, then use Privacy &amp; Security in System Settings to select Open Anyway.</li>",
                    "<li>If you use Allow and Open Speedtest Monitor.command and macOS blocks the helper itself, select Done, approve that helper with Open Anyway in Privacy &amp; Security, then run it again.</li>",
                    "<li>Read Me First - macOS Security.txt in the disk image contains the full steps and documented Terminal fallback.</li>",
                    f'<li>Install the official Speedtest CLI from <a href="{OOKLA_DOWNLOAD_URL}" target="_blank">Ookla</a>, then confirm detection under Connection Overview &gt; Measurement engine.</li>',
                    f"<li>Confirm that the controller shows version {__version__}.</li>",
                ]
            )
            security_note = (
                "The macOS release is not code-signed or notarized.  The first launch may "
                "require explicit approval in macOS security settings.  The optional "
                "approval helper is also unsigned and may require its own Open Anyway approval."
            )
        st.markdown(
            f"""
            <section class="rr-help-card">
              <h3>Run the installed monitor</h3>
              <p><strong>What to do</strong></p>
              <ol>
                <li>Open Speedtest Monitor from {launch_location}.</li>
                <li>Use Open Dashboard in the controller whenever you need to return to this page.</li>
                <li>You may close the browser tab without stopping collection.</li>
                <li>Select Quit Monitor in the controller to stop collection safely.</li>
              </ol>
              <p class="remember"><strong>Remember:</strong> Keep the Speedtest Monitor controller open while you want results collected.  A new test normally runs every five minutes, while this dashboard checks for new results every 60 seconds.</p>
            </section>
            """,
            unsafe_allow_html=True,
        )
        install_card = (
            '<section class="rr-help-card">'
            "<h3>Install or update the application</h3>"
            f"<ol>{install_steps}</ol>"
            f'<p class="remember"><strong>Unsigned release:</strong> {security_note}</p>'
            "</section>"
        )
        st.markdown(install_card, unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <section class="rr-help-card">
              <h3>Start and stop the monitor</h3>
              <p><strong>Developer mode</strong></p>
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
            <li>Review Performance Trend for changes across the selected reporting window.</li>
            <li>Drag across Performance Trend to zoom into a time span.  Zooming is limited to the time axis so the speed and ping scales are not changed accidentally.</li>
            <li>Review Latest Result for the most recent connection check.</li>
            <li>Use Connection Overview to choose the chart style, servers, reporting window, and comparison overlay.</li>
            <li>Use the Measurement engines filter to keep official Ookla, Python compatibility, and legacy samples separate.  The latest engine is selected by default.</li>
            <li>Use Test server selection to keep tests in a preferred city or region when automatic selection chooses a distant location.</li>
            <li>Use Measurement engine to confirm that the official Ookla CLI is active.  Production collection pauses rather than silently substituting another engine.</li>
            <li>Leave Refresh display every 60s enabled to see new CSV results automatically.</li>
            <li>Turn off Refresh display every 60s before selecting Refresh now for an immediate reload.</li>
            <li>Open Display settings to change timezone, theme, and chart colours.</li>
          </ol>
          <p class="remember"><strong>Data location:</strong> {DEFAULT_CSV}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <section class="rr-help-card">
          <h3>Understand the measurements</h3>
          <ul>
            <li><strong>Download</strong> measures how quickly data reaches this computer.  Higher is generally better.</li>
            <li><strong>Upload</strong> measures how quickly data leaves this computer.  Higher is generally better.</li>
            <li><strong>Ping</strong> measures response time in milliseconds.  Lower is generally better.</li>
            <li><strong>Server</strong> identifies the test location selected for that sample.  Different servers can produce different results.</li>
            <li><strong>Test engine</strong> identifies whether the official Ookla CLI or the Python fallback produced the sample.  The two engines can report materially different results and should not be treated as identical tests.</li>
          </ul>
          <p class="remember"><strong>Remember:</strong> Trends across several samples are more useful than one isolated result.</p>
        </section>
        <section class="rr-help-card">
          <h3>Data and privacy</h3>
          <ul>
            <li>Measurements are stored locally on this computer as CSV files.</li>
            <li>The dashboard is served only from the local monitor application.</li>
            <li>Closing the browser does not delete results or stop collection.</li>
            <li>The main CSV retains approximately 30 days of samples, with older monthly archives retained separately.</li>
          </ul>
          <p class="remember"><strong>Results file:</strong> {DEFAULT_CSV}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    restart_guidance = (
        (
            "Quit the monitor from its controller, then open it again from the Start menu."
            if DESKTOP_PLATFORM == "windows"
            else "Quit the monitor from its controller, then open it again from Applications."
        )
        if DESKTOP_MODE
        else "Stop with Control-C, pull the latest branch, then run the launcher again."
    )
    keep_running_guidance = (
        "Keep the Speedtest Monitor controller open if you want collection to continue."
        if DESKTOP_MODE
        else "Do not close Terminal if you want collection to continue."
    )
    browser_guidance = (
        "Reopen it from the monitor controller without interrupting collection."
        if DESKTOP_MODE
        else "Open the Local URL printed most recently in Terminal."
    )
    st.markdown(
        f"""
        <section class="rr-help-card">
          <h3>Resolve common issues</h3>
          <ul>
            <li><strong>No data yet:</strong> Confirm the collector is running and wait for its first completed test.</li>
            <li><strong>Dashboard does not update:</strong> Confirm automatic display refresh is enabled.  To force an immediate reload, turn it off and then select Refresh now.</li>
            <li><strong>Official engine required:</strong> Production mode pauses measurements when the official Ookla CLI is unavailable.  Open Measurement engine in Connection Overview to install it or set its executable path.</li>
            <li><strong>Compatibility mode:</strong> This explicit option permits the Python engine, but its results can differ materially from Ookla and should not be mixed into a like-for-like baseline.</li>
            <li><strong>Wrong test region:</strong> Open Test server selection, choose Preferred city or region, enter a city plus state, province, or country, and save.  The next collection cycle calibrates regional candidates and retains automatic fallback.</li>
            <li><strong>Automatic fallback row:</strong> All saved regional candidates were unavailable for that cycle, so the provider selected an unrestricted server.</li>
            <li><strong>Browser tab was closed:</strong> {browser_guidance}</li>
            <li><strong>Need to restart:</strong> {restart_guidance}</li>
          </ul>
          <p class="remember"><strong>Remember:</strong> {keep_running_guidance}</p>
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


def set_help_panel(open_panel: bool) -> None:
    """Open or close the non-modal Help panel."""
    st.session_state["help_panel_open"] = open_panel


if "help_panel_open" not in st.session_state:
    st.session_state["help_panel_open"] = False

with st.container(key="hero"):
    hero_copy, hero_action = st.columns([8, 1], vertical_alignment="center")
    with hero_copy:
        st.markdown(
            f"""
            <div class="rr-hero-main">
              <img class="rr-logo" src="{RAMRATTAN_LOGO_URI}" alt="Ramrattan logo">
              <div class="rr-hero-copy">
                <p class="eyebrow">RAMRATTAN NETWORK TOOLS</p>
                <h1>Speedtest Monitor</h1>
                <p>Clear, local visibility into connection speed, responsiveness, and reliability.</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hero_action:
        st.button(
            "Help with this page",
            icon=":material/help_outline:",
            help="Help with this page",
            key="open_help_panel",
            on_click=set_help_panel,
            args=(True,),
        )

if st.session_state["help_panel_open"]:
    with st.container(key="help_panel"):
        close_space, close_action = st.columns([3, 1])
        with close_action:
            st.button(
                "Close X",
                key="close_help_panel",
                width="stretch",
                on_click=set_help_panel,
                args=(False,),
            )
        render_help_panel()


def rerun_for_refresh_schedule() -> None:
    """Rebuild the app when the fragment refresh schedule changes."""
    st.rerun(scope="app")


def rerun_for_dashboard_control() -> None:
    """Apply interactive dashboard controls with a full application rerun."""
    st.rerun(scope="app")


def render_engine_settings() -> None:
    """Render the shared production engine policy and CLI discovery controls."""

    engine_settings = load_settings(DEFAULT_CSV.parent)["measurement_engine"]
    mode_options = [
        "Official Ookla CLI only (recommended)",
        "Compatibility mode (allow Python fallback)",
    ]
    configured_mode = (
        mode_options[1]
        if engine_settings["mode"] == "compatibility"
        else mode_options[0]
    )
    detected = find_ookla_cli(engine_settings["ookla_path"])

    with st.expander("Measurement engine", expanded=detected is None):
        if detected:
            st.success(f"Official Ookla CLI detected: {detected}")
        else:
            st.warning(
                "The official Ookla CLI is not available.  Production measurements "
                "are paused so the monitor does not silently mix incompatible engines."
            )
        st.link_button("Download official Ookla CLI", OOKLA_DOWNLOAD_URL)
        selected_mode = st.selectbox(
            "Engine policy",
            mode_options,
            index=mode_options.index(configured_mode),
            key="measurement_engine_mode",
            help=(
                "Official-only mode preserves a comparable baseline.  Compatibility "
                "mode uses the Python engine only when the official CLI is unavailable."
            ),
        )
        configured_path = st.text_input(
            "Official CLI executable path (optional)",
            value=engine_settings["ookla_path"],
            placeholder=(
                r"C:\Tools\OoklaSpeedtest\speedtest.exe"
                if DESKTOP_PLATFORM == "windows"
                else "/usr/local/bin/speedtest"
            ),
            key="measurement_engine_path",
            help="Leave blank to search PATH and standard installation locations.",
        )
        if st.button("Save measurement engine", key="save_measurement_engine"):
            saved_mode = (
                "compatibility" if selected_mode == mode_options[1] else "official_only"
            )
            set_measurement_engine(
                saved_mode,
                configured_path,
                DEFAULT_CSV.parent,
            )
            resolved = find_ookla_cli(configured_path)
            if resolved:
                st.success(
                    "Measurement engine saved.  The official CLI will be used on the next cycle."
                )
            elif saved_mode == "compatibility":
                st.warning(
                    "Compatibility mode saved.  The Python engine may be used until the official CLI is installed."
                )
            else:
                st.warning(
                    "Official-only mode saved.  Measurements remain paused until the CLI is available."
                )


autorefresh = bool(st.session_state.get("dashboard_auto_refresh", True))


@st.fragment(
    run_every="60s" if autorefresh else None,
    key="dashboard_data",
)
def render_dashboard() -> None:
    """Read and redraw the recorded measurements."""
    chart_mode = st.session_state.get("dashboard_chart_mode", "Bar")
    tz_name = st.session_state.get("dashboard_timezone", DEFAULT_TZ)
    if tz_name not in ALL_TZS:
        tz_name = "UTC"
    theme_options = ["Auto (Windows)", "Light", "Dark"]
    theme_choice = st.session_state.get("dashboard_theme", "Auto (Windows)")
    if theme_choice not in theme_options:
        theme_choice = "Auto (Windows)"
    theme = (
        detect_windows_theme()
        if theme_choice.startswith("Auto")
        else ("dark" if theme_choice.lower().startswith("dark") else "light")
    )
    plotly_template = apply_theme_css(theme)
    color_down = st.session_state.get("color_down", DEFAULT_COLOR_DOWNLOAD)
    color_up = st.session_state.get("color_up", DEFAULT_COLOR_UPLOAD)
    color_ping = st.session_state.get("color_ping", DEFAULT_COLOR_PING)

    df = load_data(DEFAULT_CSV)
    if df.empty:
        with st.container(border=True):
            st.info(f"No data yet.  Waiting for the collector to write results to:\n{DEFAULT_CSV}")
            st.caption("The first completed speed test will appear here automatically.")
        render_engine_settings()
        st.stop()

    latest = df.iloc[-1]
    latest_local = latest["timestamp"].tz_convert(ZoneInfo(tz_name))
    latest_server = latest["server_name"] or "Server name unavailable"
    if latest["server_id"]:
        latest_server = f'{latest["server_id"]} · {latest_server}'
    latest_engine_code = str(latest.get("engine", "") or "").strip()
    latest_engine = {
        "ookla-cli": "Official Ookla CLI",
        "python-lib": "Python fallback",
        "unknown": "Legacy or unknown engine",
    }.get(latest_engine_code, latest_engine_code or "Engine unavailable")
    latest_time_text = latest_local.strftime("%I:%M %p").lstrip("0")
    latest_date_text = latest_local.strftime("%b %d, %Y").replace(" 0", " ")

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

    engine_names = {
        "ookla-cli": "Official Ookla CLI",
        "python-lib": "Python compatibility",
        "unknown": "Legacy or unknown",
    }
    engine_codes = sorted(
        code for code in df["engine"].astype(str).unique() if code.strip()
    )
    selected_engines_key = "dashboard_selected_engines"
    last_engine_key = "dashboard_last_engine"
    previous_latest_engine = st.session_state.get(last_engine_key)
    if selected_engines_key not in st.session_state or (
        previous_latest_engine and previous_latest_engine != latest_engine_code
    ):
        st.session_state[selected_engines_key] = (
            [latest_engine_code] if latest_engine_code else engine_codes
        )
    else:
        st.session_state[selected_engines_key] = [
            code
            for code in st.session_state[selected_engines_key]
            if code in engine_codes
        ]
    st.session_state[last_engine_key] = latest_engine_code

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
    window_choices = [
        "Last Hour",
        "Last 24 hours",
        "Last 7 days",
        "Last 30 days",
        "Last 12 months",
    ]
    selected_labels = st.session_state[selected_key]
    range_choice = st.session_state.get("dashboard_window", "Last 7 days")
    if range_choice not in window_choices:
        range_choice = "Last 7 days"
    include_blank = bool(st.session_state.get("dashboard_include_blank", True))
    show_prev_overlay = bool(st.session_state.get("dashboard_previous_period", False))

    selected_engines = st.session_state[selected_engines_key]
    if selected_engines:
        df = df[df["engine"].astype(str).isin(selected_engines)]
    else:
        df = df.iloc[0:0]

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
        xaxis=dict(
            title=f"Time ({tz_name})",
            fixedrange=False,
        ),
        yaxis=dict(
            title="Speed (Mbps)",
            fixedrange=True,
        ),
        yaxis2=dict(
            title="Ping (ms)",
            overlaying="y",
            side="right",
            showgrid=False,
            fixedrange=True,
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
        f"Test engine: {latest_engine} · Display timezone: {tz_name}"
    )

    stats = (
        current_window[["download_mbps", "upload_mbps", "ping_ms"]]
        .describe()
        .T[["min", "mean", "max"]]
        .round(2)
    )
    stats.index = ["Download (Mbps)", "Upload (Mbps)", "Ping (ms)"]
    stats.columns = ["Minimum", "Average", "Peak"]

    st.markdown(
        """
        <div class="rr-section-heading rr-subsection-heading">
          <p class="eyebrow">SELECTED WINDOW</p>
          <h3>Minimum, average, and peak</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.dataframe(stats, width="stretch", height=180)
        st.caption(
            f"{len(current_window)} recorded "
            f"{'sample' if len(current_window) == 1 else 'samples'} in this view.  "
            "Peak is the highest recorded value.  For ping, the minimum is best."
        )

    st.markdown(
        """
        <div class="rr-section-heading">
          <p class="eyebrow">CONNECTION OVERVIEW</p>
          <h2>Internet performance controls</h2>
          <p>Adjust the chart, refresh schedule, display, servers, and reporting window.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        control_chart, control_refresh, control_manual = st.columns(
            [1.8, 1.35, 1],
            gap="large",
        )
        with control_chart:
            st.radio(
                "Chart type",
                ["Bar", "Line / Curve"],
                index=0,
                horizontal=True,
                key="dashboard_chart_mode",
                on_change=rerun_for_dashboard_control,
            )
        with control_refresh:
            st.toggle(
                "Refresh display every 60s",
                value=True,
                key="dashboard_auto_refresh",
                on_change=rerun_for_refresh_schedule,
            )
        with control_manual:
            st.write("")
            st.button(
                "Refresh now",
                type="primary",
                key="refresh_now_btn",
                width="stretch",
                disabled=autorefresh,
                help=(
                    "Turn off Refresh display every 60s to use manual refresh."
                    if autorefresh
                    else "Reload the dashboard data now."
                ),
                on_click=rerun_for_dashboard_control,
            )

    with st.expander("Display settings", expanded=False):
        setting_timezone, setting_theme = st.columns(2, gap="large")
        with setting_timezone:
            st.selectbox(
                "Timezone",
                ALL_TZS,
                index=ALL_TZS.index(tz_name),
                key="dashboard_timezone",
            )
        with setting_theme:
            st.selectbox(
                "Theme",
                theme_options,
                index=theme_options.index(theme_choice),
                key="dashboard_theme",
            )

        st.markdown("**Chart colours**")
        colc1, colc2, colc3 = st.columns(3)
        with colc1:
            st.color_picker(
                "Download",
                DEFAULT_COLOR_DOWNLOAD,
                key="color_down",
            )
        with colc2:
            st.color_picker(
                "Upload",
                DEFAULT_COLOR_UPLOAD,
                key="color_up",
            )
        with colc3:
            st.color_picker(
                "Ping",
                DEFAULT_COLOR_PING,
                key="color_ping",
            )

    render_engine_settings()

    server_settings = load_settings(DEFAULT_CSV.parent)["server_selection"]
    server_mode_options = ["Automatic", "Preferred city or region"]
    configured_mode = (
        "Preferred city or region"
        if server_settings["mode"] == "preferred_area"
        else "Automatic"
    )
    with st.expander("Test server selection", expanded=False):
        st.caption(
            "Automatic uses the speed-test provider's public-IP location.  "
            "Choose a preferred area if that location is inaccurate."
        )
        preference_mode = st.selectbox(
            "Selection mode",
            server_mode_options,
            index=server_mode_options.index(configured_mode),
            key="server_preference_mode",
        )
        preferred_area = st.text_input(
            "Preferred city or region",
            value=server_settings["area"],
            placeholder="For example: Austin, TX",
            disabled=preference_mode == "Automatic",
            key="server_preference_area",
            help="Use a city plus state, province, or country.  No street address is needed or stored.",
        )
        if st.button("Save test server preference", key="save_server_preference"):
            if preference_mode != "Automatic" and not preferred_area.strip():
                st.error("Enter a city and state, province, or country before saving.")
            else:
                saved_settings = set_server_preference(
                    "preferred_area" if preference_mode != "Automatic" else "automatic",
                    preferred_area,
                    DEFAULT_CSV.parent,
                )
                server_settings = saved_settings["server_selection"]
                if preference_mode == "Automatic":
                    st.success("Automatic server selection is active.")
                else:
                    st.success(
                        "Preference saved.  The next measurement will calibrate regional servers."
                    )

        if server_settings["mode"] == "preferred_area":
            if server_settings["server_labels"]:
                st.caption(
                    f"Active area: {server_settings['area']}.  "
                    f"Calibrated candidates: {len(server_settings['server_labels'])}."
                )
                st.caption(f"Primary server: {server_settings['server_labels'][0]}")
            elif server_settings["last_error"]:
                st.warning(
                    f"Last calibration failed: {server_settings['last_error']}  "
                    "Update the area or save again to retry."
                )
            else:
                st.caption(
                    f"Waiting to calibrate servers for {server_settings['area']} during the next measurement."
                )

    with st.expander("View options", expanded=True):
        filter_servers, filter_engines, filter_window = st.columns(
            [2.0, 1.1, 1],
            gap="large",
        )
        with filter_servers:
            st.multiselect(
                "Servers",
                server_labels,
                key=selected_key,
            )
        with filter_engines:
            st.multiselect(
                "Measurement engines",
                engine_codes,
                key=selected_engines_key,
                format_func=lambda code: engine_names.get(code, code),
                help="The latest engine is selected by default so incompatible methods are not mixed.",
            )
        with filter_window:
            st.selectbox(
                "Show window",
                window_choices,
                index=window_choices.index(range_choice),
                key="dashboard_window",
            )

        option_blank, option_overlay = st.columns(2)
        with option_blank:
            st.checkbox(
                "Include results without a server ID",
                value=True,
                help="Include rows with no server ID or server name.",
                key="dashboard_include_blank",
            )
        with option_overlay:
            st.checkbox(
                "Show previous period",
                value=False,
                help="Compare against the immediately preceding period of the same length.",
                key="dashboard_previous_period",
            )
        st.caption(f"{sample_caption}  Data retained for 30 days in the main CSV.")

render_dashboard()

st.caption(
    "Ramrattan Speedtest Monitor · Local data only · "
    "Use Help for operating guidance and troubleshooting."
)
