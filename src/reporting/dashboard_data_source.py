"""Data source helpers for local and published dashboard inputs."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pandas as pd

from .dashboard_settings import DashboardSettings

DashboardLocation = str | Path

DATASET_RELATIVE_PATHS: dict[str, PurePosixPath] = {
    "clean_sales_data": PurePosixPath("transformation/clean_sales_data.csv"),
    "quality": PurePosixPath("analytics/analytics_quality.csv"),
    "file_inventory": PurePosixPath("analytics/analytics_file_inventory.csv"),
}


def get_dataset_locations(settings: DashboardSettings) -> dict[str, DashboardLocation]:
    """Return the dashboard CSV locations for the active source mode."""
    if settings.mode == "github_raw":
        base_url = settings.remote_data_base_url.rstrip("/")
        return {
            name: f"{base_url}/{relative_path.as_posix()}"
            for name, relative_path in DATASET_RELATIVE_PATHS.items()
        }

    local_root = settings.local_data_root
    return {
        name: local_root / Path(relative_path)
        for name, relative_path in DATASET_RELATIVE_PATHS.items()
    }


def get_dataset_signatures(
    locations: dict[str, DashboardLocation],
) -> tuple[str, ...]:
    """Build cache signatures from local files or remote URLs."""
    signatures: list[str] = []
    for name, location in locations.items():
        if isinstance(location, Path):
            signatures.append(f"{name}:{location}:{location.stat().st_mtime_ns}")
        else:
            signatures.append(f"{name}:{location}")
    return tuple(signatures)


def describe_data_sources(settings: DashboardSettings) -> dict[str, str]:
    """Return user-facing descriptions of the configured data source."""
    if settings.mode == "github_raw":
        return {
            "Mode": "Donnees publiees sur GitHub (simulation d'un partage central)",
            "Source": settings.remote_data_base_url,
        }

    return {
        "Mode": "Dossier local du runtime",
        "Transformation": str(settings.local_data_root / "transformation"),
        "Analytics": str(settings.local_data_root / "analytics"),
    }


def load_dashboard_frames(
    locations: dict[str, DashboardLocation],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the CSV files required by the dashboard."""
    missing_files = [
        str(location)
        for location in locations.values()
        if isinstance(location, Path) and not location.exists()
    ]
    if missing_files:
        raise FileNotFoundError(
            "Missing reporting inputs: " + ", ".join(missing_files)
        )

    try:
        clean_df = pd.read_csv(locations["clean_sales_data"])
        quality_df = pd.read_csv(locations["quality"])
        file_inventory_df = pd.read_csv(locations["file_inventory"])
    except Exception as error:  # pragma: no cover - defensive I/O guard
        raise RuntimeError(
            "Impossible de charger les donnees du dashboard depuis la source "
            f"configuree: {error}"
        ) from error

    return clean_df, quality_df, file_inventory_df
