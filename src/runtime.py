"""Runtime path helpers for packaged and deployed executions."""

from __future__ import annotations

import os
from pathlib import Path

RUNTIME_ROOT_ENV = "SALES_PIPELINE_RUNTIME_ROOT"
LOG_FILE_ENV = "SALES_PIPELINE_LOG_FILE"


def get_runtime_root(runtime_root: Path | None = None) -> Path:
    """Return the runtime root used for inputs, outputs, and logs."""
    if runtime_root is not None:
        return runtime_root.expanduser().resolve()

    runtime_root_env = os.getenv(RUNTIME_ROOT_ENV)
    if runtime_root_env:
        return Path(runtime_root_env).expanduser().resolve()

    return Path.cwd().resolve()


def get_raw_sales_data_dir(runtime_root: Path | None = None) -> Path:
    """Return the raw input directory for sales Excel files."""
    return get_runtime_root(runtime_root) / "raw_sales_data"


def get_outputs_root(runtime_root: Path | None = None) -> Path:
    """Return the output root directory for generated artifacts."""
    return get_runtime_root(runtime_root) / "outputs"


def get_default_log_file(runtime_root: Path | None = None) -> Path:
    """Return the default log file path for batch executions."""
    custom_log_file = os.getenv(LOG_FILE_ENV)
    if custom_log_file:
        return Path(custom_log_file).expanduser().resolve()

    return get_outputs_root(runtime_root) / "logs" / "pipeline.log"
