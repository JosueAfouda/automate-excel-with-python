"""Publish pipeline CSV outputs into the tracked dashboard data folder."""

from __future__ import annotations

import argparse
from pathlib import Path
from shutil import copy2
import sys

from src.runtime import get_outputs_root, get_runtime_root

PUBLISHED_FILES: tuple[tuple[Path, Path], ...] = (
    (Path("analytics/analytics_file_inventory.csv"), Path("analytics/analytics_file_inventory.csv")),
    (Path("analytics/analytics_quality.csv"), Path("analytics/analytics_quality.csv")),
    (Path("analytics/kpi_overview.csv"), Path("analytics/kpi_overview.csv")),
    (Path("analytics/kpis_by_plan.csv"), Path("analytics/kpis_by_plan.csv")),
    (Path("analytics/kpis_by_store.csv"), Path("analytics/kpis_by_store.csv")),
    (Path("analytics/monthly_kpis.csv"), Path("analytics/monthly_kpis.csv")),
    (Path("transformation/clean_sales_data.csv"), Path("transformation/clean_sales_data.csv")),
)


def publish_dashboard_data(
    *,
    source_root: Path,
    publish_root: Path,
) -> list[Path]:
    """Copy the latest pipeline outputs into the tracked publication folder."""
    copied_files: list[Path] = []
    for source_relative, target_relative in PUBLISHED_FILES:
        source_path = source_root / source_relative
        target_path = publish_root / target_relative
        if not source_path.exists():
            raise FileNotFoundError(f"Missing publish source file: {source_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, target_path)
        copied_files.append(target_path)
    return copied_files


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-dashboard-publish-data",
        description="Copy the latest dashboard CSV inputs into the tracked publication folder.",
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="Optional runtime root containing outputs/.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Optional override for the source outputs root.",
    )
    parser.add_argument(
        "--publish-root",
        type=Path,
        default=None,
        help="Optional override for the publication root directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        runtime_root = get_runtime_root(args.runtime_root)
        source_root = args.source_root or get_outputs_root(runtime_root)
        publish_root = args.publish_root or (runtime_root / "published_data")
        copied_files = publish_dashboard_data(
            source_root=source_root,
            publish_root=publish_root,
        )
        print(f"SOURCE_ROOT={source_root}")
        print(f"PUBLISH_ROOT={publish_root}")
        print(f"PUBLISHED_FILES={len(copied_files)}")
        for copied_file in copied_files:
            print(f"PUBLISHED_FILE={copied_file}")
        return 0
    except Exception as error:  # pragma: no cover - defensive CLI guard
        print(f"ERROR_MESSAGE={error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
