from dataclasses import dataclass
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = [
    "transaction_id",
    "store",
    "transaction_date",
    "plan",
    "contract_type",
    "amount",
]
OPTIONAL_COLUMNS = ["status"]
INGESTION_DATA_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS + [
    "source_file",
    "source_folder",
]


@dataclass
class IngestionResult:
    # data metier
    data: pd.DataFrame

    # metadonnees d'ingestion
    file_inventory: pd.DataFrame


def get_project_root() -> Path:
    """Return the root folder of the project."""
    return Path(__file__).resolve().parents[2]


def discover_excel_files(source_dir: Path | None = None) -> list[Path]:
    """Find sales Excel files in the raw input folder."""
    target_dir = source_dir or get_project_root() / "raw_sales_data"

    if not target_dir.exists():
        logger.warning("Source directory does not exist: %s", target_dir)
        return []

    files = [
        *sorted(target_dir.glob("*.xls")),
        *sorted(target_dir.glob("*.xlsx")),
    ]

    return [file_path for file_path in files if not file_path.name.startswith("~$")]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and ensure expected columns exist."""
    normalized = df.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]

    for missing in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if missing not in normalized.columns:
            normalized[missing] = pd.NA

    ordered_columns = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    other_columns = [
        column for column in normalized.columns
        if column not in ordered_columns
    ]
    return normalized[ordered_columns + other_columns]


def empty_ingestion_data() -> pd.DataFrame:
    """Return an empty DataFrame with the ingestion data columns."""
    return pd.DataFrame(columns=INGESTION_DATA_COLUMNS)


def load_sales_files(files: list[Path]) -> IngestionResult:
    """Load, normalize, and combine the provided sales Excel files."""
    if not files:
        raise ValueError("No sales Excel files were provided for ingestion.")

    logger.info("Loading %s sales file(s)", len(files))
    parts: list[pd.DataFrame] = []
    inventory_rows: list[dict[str, object]] = []

    for file_path in files:
        try:
            logger.info("Reading sales file %s", file_path)
            raw = pd.read_excel(file_path)
            normalized = normalize_columns(raw)

            normalized["source_file"] = file_path.name
            normalized["source_folder"] = file_path.parent.name

            parts.append(normalized)
            inventory_rows.append(
                {
                    "source_file": file_path.name,
                    "source_folder": file_path.parent.name,
                    "rows_loaded": len(normalized),
                    "status": "loaded",
                }
            )
            logger.info("Loaded %s row(s) from %s", len(normalized), file_path.name)
        except Exception as error:
            logger.exception("Failed to load sales file %s", file_path)
            inventory_rows.append(
                {
                    "source_file": file_path.name,
                    "source_folder": file_path.parent.name,
                    "rows_loaded": 0,
                    "status": "error",
                    "error": str(error),
                }
            )

    combined = (
        pd.concat(parts, ignore_index=True)
        if parts
        else empty_ingestion_data()
    )

    inventory = pd.DataFrame(inventory_rows).sort_values(
        ["source_folder", "source_file"]
    )

    return IngestionResult(data=combined, file_inventory=inventory)


def load_sales_data(source_dir: Path | None = None) -> IngestionResult:
    """Load, normalize, and combine all sales Excel files in the source folder."""
    files = discover_excel_files(source_dir)

    if not files:
        raise FileNotFoundError(
            "No sales Excel files were found in the configured source folder."
        )

    return load_sales_files(files)
