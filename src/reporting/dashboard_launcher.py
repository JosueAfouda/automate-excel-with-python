"""Launcher used for `sales-dashboard` and the PyInstaller executable."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from streamlit.web import bootstrap

from .dashboard_settings import (
    DASHBOARD_CONFIG_ENV,
    DASHBOARD_RUNTIME_ROOT_ENV,
    load_dashboard_settings,
)


def _detect_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd().resolve()


def _resolve_streamlit_script() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        frozen_path = Path(sys._MEIPASS) / "src" / "reporting" / "streamlit_app.py"
        if frozen_path.exists():
            return frozen_path
    return Path(__file__).with_name("streamlit_app.py")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-dashboard",
        description="Launch the packaged Streamlit dashboard.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional dashboard TOML configuration file.",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="Optional runtime root used to resolve config and local output folders.",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=None,
        help="Optional override for the Streamlit HTTP port.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Force headless mode for non-interactive launches.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    runtime_root = (args.runtime_root or _detect_runtime_root()).expanduser().resolve()
    os.environ[DASHBOARD_RUNTIME_ROOT_ENV] = str(runtime_root)
    if args.config is not None:
        os.environ[DASHBOARD_CONFIG_ENV] = str(args.config.expanduser().resolve())

    settings = load_dashboard_settings(
        config_path=args.config,
        runtime_root=runtime_root,
    )

    flag_options = {
        "server.port": args.server_port or settings.server_port,
        "server.headless": args.headless or settings.headless,
        "browser.gatherUsageStats": False,
    }
    bootstrap.run(
        str(_resolve_streamlit_script()),
        False,
        [],
        flag_options,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
