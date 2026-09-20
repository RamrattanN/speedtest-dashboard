from PyInstaller.utils.hooks import collect_all


streamlit_datas, streamlit_binaries, streamlit_hiddenimports = collect_all("streamlit")
plotly_datas, plotly_binaries, plotly_hiddenimports = collect_all("plotly")

a = Analysis(
    ["src/speedtest_dashboard/macos_app.py"],
    pathex=["src"],
    binaries=streamlit_binaries + plotly_binaries,
    datas=(
        streamlit_datas
        + plotly_datas
        + [
            ("src/speedtest_dashboard/dashboard.py", "speedtest_dashboard"),
            (
                "src/speedtest_dashboard/assets/ramrattan-logo.png.b64",
                "speedtest_dashboard/assets",
            ),
        ]
    ),
    hiddenimports=(
        streamlit_hiddenimports
        + plotly_hiddenimports
        + [
            "speedtest",
            "speedtest_dashboard.collector",
            "speedtest_dashboard.dashboard",
            "tzdata",
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Speedtest Monitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    icon="build/macos-icon/SpeedtestMonitor.icns",
    target_arch="x86_64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Speedtest Monitor",
)

app = BUNDLE(
    coll,
    name="Speedtest Monitor.app",
    icon="build/macos-icon/SpeedtestMonitor.icns",
    bundle_identifier="com.ramrattan.speedtest-monitor",
    info_plist={
        "CFBundleDisplayName": "Speedtest Monitor",
        "CFBundleShortVersionString": "0.2.0-pilot",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
    },
)
