"""Configuration helpers for the packaged Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from src.runtime import get_runtime_root

DASHBOARD_CONFIG_ENV = "SALES_DASHBOARD_CONFIG"
DASHBOARD_RUNTIME_ROOT_ENV = "SALES_DASHBOARD_RUNTIME_ROOT"
DASHBOARD_MODE_ENV = "SALES_DASHBOARD_MODE"

DEFAULT_REMOTE_DATA_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "JosueAfouda/automate-excel-with-python/executable/streamlit/published_data"
)
DEFAULT_RELEASE_MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "JosueAfouda/automate-excel-with-python/executable/streamlit/"
    "published_app/dashboard_release.json"
)


@dataclass(frozen=True)
class DashboardSettings:
    """Resolved settings used by the dashboard runtime."""

    config_path: Path | None
    runtime_root: Path
    mode: str
    local_data_root: Path
    remote_data_base_url: str
    release_manifest_url: str
    check_for_updates: bool
    auto_open_browser: bool
    server_port: int
    headless: bool


def _resolve_optional_path(raw_value: str | None, *, base_dir: Path) -> Path | None:
    if not raw_value:
        return None

    path = Path(raw_value).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    return path


def _load_config_file(config_path: Path | None) -> dict[str, object]:
    if config_path is None or not config_path.exists():
        return {}

    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def _get_default_config_path(runtime_root: Path) -> Path | None:
    candidates = [
        runtime_root / "dashboard_config.toml",
        runtime_root / "config" / "dashboard_local.toml",
        runtime_root / "config" / "dashboard_github.toml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _coerce_bool(raw_value: object, default: bool) -> bool:
    if raw_value is None:
        return default
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw_value)


def load_dashboard_settings(
    *,
    config_path: Path | None = None,
    runtime_root: Path | None = None,
) -> DashboardSettings:
    """Load dashboard settings from CLI args, env vars, and TOML config."""
    initial_runtime_root = get_runtime_root(
        runtime_root
        or (
            Path(os.environ[DASHBOARD_RUNTIME_ROOT_ENV]).expanduser()
            if os.getenv(DASHBOARD_RUNTIME_ROOT_ENV)
            else None
        )
    )

    config_path_value = config_path
    if config_path_value is None:
        config_env = os.getenv(DASHBOARD_CONFIG_ENV)
        if config_env:
            config_path_value = Path(config_env).expanduser().resolve()
        else:
            config_path_value = _get_default_config_path(initial_runtime_root)
    elif not config_path_value.exists():
        raise FileNotFoundError(f"Dashboard config file does not exist: {config_path_value}")

    if config_path_value is not None and not config_path_value.exists():
        raise FileNotFoundError(f"Dashboard config file does not exist: {config_path_value}")

    config_data = _load_config_file(config_path_value)
    dashboard_section = config_data.get("dashboard", {}) if isinstance(config_data, dict) else {}
    if not isinstance(dashboard_section, dict):
        dashboard_section = {}

    config_base_dir = (
        config_path_value.parent.resolve()
        if config_path_value is not None
        else initial_runtime_root
    )

    configured_runtime_root = _resolve_optional_path(
        dashboard_section.get("runtime_root") if dashboard_section else None,
        base_dir=config_base_dir,
    )
    resolved_runtime_root = get_runtime_root(runtime_root or configured_runtime_root)

    mode = str(
        os.getenv(DASHBOARD_MODE_ENV)
        or dashboard_section.get("mode", "local")
    ).strip().lower()
    if mode not in {"local", "github_raw"}:
        raise ValueError(f"Unsupported dashboard mode: {mode}")

    local_data_root = _resolve_optional_path(
        dashboard_section.get("local_data_root") if dashboard_section else None,
        base_dir=config_base_dir,
    ) or (resolved_runtime_root / "outputs")

    remote_data_base_url = str(
        dashboard_section.get("remote_data_base_url", DEFAULT_REMOTE_DATA_BASE_URL)
    ).rstrip("/")
    release_manifest_url = str(
        dashboard_section.get("release_manifest_url", DEFAULT_RELEASE_MANIFEST_URL)
    ).strip()

    check_for_updates = _coerce_bool(
        dashboard_section.get("check_for_updates"),
        True,
    )
    auto_open_browser = _coerce_bool(
        dashboard_section.get("auto_open_browser"),
        True,
    )
    server_port = int(dashboard_section.get("server_port", 8501))
    headless = _coerce_bool(
        dashboard_section.get("headless"),
        False,
    )

    return DashboardSettings(
        config_path=config_path_value,
        runtime_root=resolved_runtime_root,
        mode=mode,
        local_data_root=local_data_root,
        remote_data_base_url=remote_data_base_url,
        release_manifest_url=release_manifest_url,
        check_for_updates=check_for_updates,
        auto_open_browser=auto_open_browser,
        server_port=server_port,
        headless=headless,
    )
