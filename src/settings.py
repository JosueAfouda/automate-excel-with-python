"""Configuration loading for packaged pipeline executions."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from .runtime import get_default_log_file, get_runtime_root

CONFIG_PATH_ENV = "SALES_PIPELINE_CONFIG"


@dataclass(frozen=True)
class PipelineSettings:
    """Resolved runtime settings for a pipeline execution."""

    config_path: Path | None
    runtime_root: Path
    source_dir: Path
    ingestion_output_dir: Path
    log_file: Path
    environment: str


def _resolve_optional_path(
    raw_value: str | None,
    *,
    base_dir: Path,
) -> Path | None:
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
    candidate_path = runtime_root / "config" / "prod.toml"
    if candidate_path.exists():
        return candidate_path
    return None


def load_settings(
    *,
    config_path: Path | None = None,
    runtime_root: Path | None = None,
    source_dir: Path | None = None,
    output_dir: Path | None = None,
    log_file: Path | None = None,
) -> PipelineSettings:
    """Load runtime settings from CLI args, environment, and TOML config."""
    initial_runtime_root = get_runtime_root(runtime_root)

    config_path_value = config_path
    if config_path_value is None:
        config_env = os.getenv(CONFIG_PATH_ENV)
        if config_env:
            config_path_value = Path(config_env).expanduser().resolve()
        else:
            config_path_value = _get_default_config_path(initial_runtime_root)
    elif not config_path_value.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {config_path_value}")

    if config_path_value is not None and not config_path_value.exists():
        raise FileNotFoundError(f"Configuration file does not exist: {config_path_value}")

    config_data = _load_config_file(config_path_value)
    runtime_section = config_data.get("runtime", {}) if isinstance(config_data, dict) else {}
    if not isinstance(runtime_section, dict):
        runtime_section = {}

    config_base_dir = (
        config_path_value.parent.resolve()
        if config_path_value is not None
        else initial_runtime_root
    )

    configured_runtime_root = _resolve_optional_path(
        runtime_section.get("runtime_root") if runtime_section else None,
        base_dir=config_base_dir,
    )
    resolved_runtime_root = get_runtime_root(runtime_root or configured_runtime_root)

    resolved_source_dir = source_dir or _resolve_optional_path(
        runtime_section.get("source_dir") if runtime_section else None,
        base_dir=config_base_dir,
    ) or (resolved_runtime_root / "raw_sales_data")

    resolved_output_dir = output_dir or _resolve_optional_path(
        runtime_section.get("ingestion_output_dir") if runtime_section else None,
        base_dir=config_base_dir,
    ) or (resolved_runtime_root / "outputs" / "ingestion")

    resolved_log_file = log_file or _resolve_optional_path(
        runtime_section.get("log_file") if runtime_section else None,
        base_dir=config_base_dir,
    ) or get_default_log_file(resolved_runtime_root)

    environment = str(runtime_section.get("environment", "prod"))

    return PipelineSettings(
        config_path=config_path_value,
        runtime_root=resolved_runtime_root,
        source_dir=resolved_source_dir,
        ingestion_output_dir=resolved_output_dir,
        log_file=resolved_log_file,
        environment=environment,
    )
