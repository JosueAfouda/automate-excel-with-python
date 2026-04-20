"""Command-line entrypoints for pipeline operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import PipelineRunResult, run_pipeline
from .settings import load_settings


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales-pipeline",
        description="Run or validate the Excel sales pipeline runtime.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Execute the pipeline and generate the latest report.",
    )
    run_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML configuration file for Ops/runtime settings.",
    )
    run_parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="Working directory containing raw_sales_data/ and outputs/.",
    )
    run_parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Optional override for the raw sales input directory.",
    )
    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override for the ingestion output directory.",
    )
    run_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional override for the pipeline log file path.",
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Validate the runtime layout before scheduling or executing the job.",
    )
    check_parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional TOML configuration file for Ops/runtime settings.",
    )
    check_parser.add_argument(
        "--runtime-root",
        type=Path,
        default=None,
        help="Working directory containing raw_sales_data/ and outputs/.",
    )
    return parser


def _print_run_summary(result: PipelineRunResult, log_file: Path) -> None:
    print("PIPELINE_STATUS=SUCCESS")
    print(f"LOG_FILE={log_file}")
    print(f"NEW_FILES_PROCESSED={result.new_files_processed}")
    print(f"FILES_SKIPPED={result.skipped_files}")
    print(f"ROWS_INGESTED={result.rows_ingested}")
    print(f"ROWS_CLEANED={result.rows_cleaned}")
    print(f"ROWS_ANALYZED={result.rows_analyzed}")
    for output_name, output_path in result.output_paths.items():
        print(f"OUTPUT_{output_name.upper()}={output_path}")


def _run_command(args: argparse.Namespace) -> int:
    settings = load_settings(
        config_path=args.config,
        runtime_root=args.runtime_root,
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        log_file=args.log_file,
    )
    result = run_pipeline(
        output_dir=settings.ingestion_output_dir,
        source_dir=settings.source_dir,
        runtime_root=settings.runtime_root,
        log_file=settings.log_file,
    )
    print(f"CONFIG_PATH={settings.config_path or 'DEFAULTS'}")
    print(f"ENVIRONMENT={settings.environment}")
    print(f"RUNTIME_ROOT={settings.runtime_root}")
    print(f"SOURCE_DIR={settings.source_dir}")
    print(f"INGESTION_OUTPUT_DIR={settings.ingestion_output_dir}")
    _print_run_summary(result, settings.log_file)
    return 0


def _check_command(args: argparse.Namespace) -> int:
    settings = load_settings(
        config_path=args.config,
        runtime_root=args.runtime_root,
    )
    runtime_root = settings.runtime_root
    source_dir = settings.source_dir
    outputs_dir = settings.ingestion_output_dir.parent
    log_file = settings.log_file

    print(f"CONFIG_PATH={settings.config_path or 'DEFAULTS'}")
    print(f"ENVIRONMENT={settings.environment}")
    print(f"RUNTIME_ROOT={runtime_root}")
    print(f"SOURCE_DIR={source_dir}")
    print(f"OUTPUTS_DIR={outputs_dir}")
    print(f"INGESTION_OUTPUT_DIR={settings.ingestion_output_dir}")
    print(f"DEFAULT_LOG_FILE={log_file}")

    if not source_dir.exists():
        print("CHECK_STATUS=ERROR")
        print(f"CHECK_MESSAGE=Source directory does not exist: {source_dir}")
        return 1

    excel_files = [
        path for path in sorted(source_dir.iterdir())
        if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"} and not path.name.startswith("~$")
    ]
    print(f"EXCEL_FILES_FOUND={len(excel_files)}")

    outputs_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    print("CHECK_STATUS=SUCCESS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run":
            return _run_command(args)
        if args.command == "check":
            return _check_command(args)
        parser.error(f"Unsupported command: {args.command}")
    except Exception as error:  # pragma: no cover - defensive CLI guard
        print("PIPELINE_STATUS=ERROR", file=sys.stderr)
        print(f"ERROR_MESSAGE={error}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
