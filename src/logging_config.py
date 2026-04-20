import logging
from pathlib import Path

from .runtime import get_default_log_file


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_project_root() -> Path:
    """Return the root folder of the project."""
    return Path(__file__).resolve().parents[1]


def configure_logging(
    log_file: Path | None = None,
    runtime_root: Path | None = None,
) -> Path:
    """Configure file logging for the pipeline and return the log file path."""
    target_log_file = log_file or get_default_log_file(runtime_root)
    target_log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    resolved_log_file = str(target_log_file.resolve())

    for handler in root_logger.handlers:
        if getattr(handler, "_pipeline_log_file", None) == resolved_log_file:
            return target_log_file

    file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler._pipeline_log_file = resolved_log_file
    root_logger.addHandler(file_handler)

    return target_log_file
