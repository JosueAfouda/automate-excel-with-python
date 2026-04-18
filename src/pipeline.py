from dataclasses import dataclass
import logging
from pathlib import Path

import pandas as pd

from .logging_config import configure_logging
from .transformation.cleaning import CleaningResult, clean_sales_data

from .ingestion.sales_ingestion import (
    IngestionResult,
    discover_excel_files,
    load_sales_files,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineRunResult:
    """Summary of a pipeline run."""
    output_paths: dict[str, Path]
    new_files_processed: int
    skipped_files: int
    rows_ingested: int
    rows_cleaned: int


def get_project_root() -> Path:
    """Return the root folder of the project."""
    return Path(__file__).resolve().parents[1]


def get_output_paths(output_dir: Path) -> dict[str, Path]:
    """Return the CSV output paths for the ingestion step."""
    return {
        "business_data": output_dir / "business_data.csv",
        "ingestion_metadata": output_dir / "ingestion_metadata.csv",
    }


def get_transformation_output_paths(output_dir: Path) -> dict[str, Path]:
    """Return the CSV output paths for the transformation step."""
    return {
        "clean_sales_data": output_dir / "clean_sales_data.csv",
    }


def read_ingestion_metadata(metadata_path: Path) -> pd.DataFrame:
    """Load the ingestion metadata file if it exists."""
    if not metadata_path.exists():
        logger.info("No ingestion metadata found at %s. Full load will be used.", metadata_path)
        return pd.DataFrame(
            columns=["source_file", "source_folder", "rows_loaded", "status"]
        )

    logger.info("Loading ingestion metadata from %s", metadata_path)
    return pd.read_csv(metadata_path)


def get_loaded_file_keys(ingestion_metadata: pd.DataFrame) -> set[tuple[str, str]]:
    """Return the set of files already loaded successfully."""
    if ingestion_metadata.empty or "source_file" not in ingestion_metadata.columns:
        return set()

    loaded_rows = ingestion_metadata.copy()
    if "status" in loaded_rows.columns:
        loaded_rows = loaded_rows[loaded_rows["status"] == "loaded"]

    if "source_folder" in loaded_rows.columns:
        source_folders = loaded_rows["source_folder"].fillna("").astype(str)
    else:
        source_folders = pd.Series([""] * len(loaded_rows), index=loaded_rows.index)

    source_files = loaded_rows["source_file"].fillna("").astype(str)
    return set(zip(source_folders, source_files))


def filter_new_files(
    available_files: list[Path],
    loaded_file_keys: set[tuple[str, str]],
) -> list[Path]:
    """Keep only files that are not already present in the ingestion metadata."""
    return [
        file_path
        for file_path in available_files
        if (file_path.parent.name, file_path.name) not in loaded_file_keys
    ]


def read_business_data(business_data_path: Path) -> pd.DataFrame:
    """Load the business data CSV if it exists."""
    if not business_data_path.exists():
        return pd.DataFrame()

    return pd.read_csv(business_data_path)


def merge_business_data(
    business_data_path: Path,
    new_data: pd.DataFrame,
) -> pd.DataFrame:
    """Append newly ingested rows to the existing business data output."""
    if not business_data_path.exists():
        logger.info("No existing business data found at %s", business_data_path)
        return new_data

    existing_data = read_business_data(business_data_path)
    if new_data.empty:
        return existing_data

    return pd.concat([existing_data, new_data], ignore_index=True)


def merge_ingestion_metadata(
    existing_metadata: pd.DataFrame,
    new_metadata: pd.DataFrame,
) -> pd.DataFrame:
    """Merge the historical and newly generated ingestion metadata."""
    if existing_metadata.empty:
        combined = new_metadata.copy()
    elif new_metadata.empty:
        combined = existing_metadata.copy()
    else:
        combined = pd.concat([existing_metadata, new_metadata], ignore_index=True, sort=False)

    if combined.empty:
        return combined

    deduplication_columns = [
        column
        for column in ["source_folder", "source_file"]
        if column in combined.columns
    ]
    if deduplication_columns:
        combined = combined.drop_duplicates(
            subset=deduplication_columns,
            keep="last",
        )

    sorting_columns = [
        column
        for column in ["source_folder", "source_file"]
        if column in combined.columns
    ]
    if sorting_columns:
        combined = combined.sort_values(sorting_columns).reset_index(drop=True)

    return combined


def validate_incremental_outputs(output_paths: dict[str, Path]) -> None:
    """Validate that the incremental output files are in a consistent state."""
    business_data_exists = output_paths["business_data"].exists()
    ingestion_metadata_exists = output_paths["ingestion_metadata"].exists()

    if business_data_exists == ingestion_metadata_exists:
        return

    logger.error(
        "Inconsistent incremental state: business_data exists=%s, ingestion_metadata exists=%s",
        business_data_exists,
        ingestion_metadata_exists,
    )
    raise FileNotFoundError(
        "Incremental ingestion state is inconsistent. "
        "Both business_data.csv and ingestion_metadata.csv must exist together."
    )


def save_ingestion_outputs(
    ingestion_result: IngestionResult,
    output_dir: Path,
) -> dict[str, Path]:
    """Save ingestion outputs to CSV files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = get_output_paths(output_dir)

    logger.info("Writing business data to %s", output_paths["business_data"])
    ingestion_result.data.to_csv(output_paths["business_data"], index=False)
    logger.info("Writing ingestion metadata to %s", output_paths["ingestion_metadata"])
    ingestion_result.file_inventory.to_csv(output_paths["ingestion_metadata"], index=False)

    return output_paths


def save_transformation_outputs(
    cleaning_result: CleaningResult,
    output_dir: Path,
) -> dict[str, Path]:
    """Save transformation outputs to CSV files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = get_transformation_output_paths(output_dir)

    logger.info("Writing clean sales data to %s", output_paths["clean_sales_data"])
    cleaning_result.data.to_csv(output_paths["clean_sales_data"], index=False)

    return output_paths


def run_pipeline(
    output_dir: Path | None = None,
    source_dir: Path | None = None,
) -> PipelineRunResult:
    """Run the current pipeline and return the generated file paths."""
    log_file = configure_logging()
    ingestion_output_dir = output_dir or get_project_root() / "outputs" / "ingestion"
    transformation_output_dir = get_project_root() / "outputs" / "transformation"
    ingestion_output_paths = get_output_paths(ingestion_output_dir)
    logger.info("File logging configured at %s", log_file)
    logger.info("Starting pipeline run with ingestion output directory %s", ingestion_output_dir)
    validate_incremental_outputs(ingestion_output_paths)

    available_files = discover_excel_files(source_dir)
    if not available_files:
        logger.error("No sales Excel files found in source directory %s", source_dir)
        raise FileNotFoundError(
            "No sales Excel files were found in the configured source folder."
        )

    logger.info("Discovered %s sales file(s)", len(available_files))
    existing_metadata = read_ingestion_metadata(ingestion_output_paths["ingestion_metadata"])
    loaded_file_keys = get_loaded_file_keys(existing_metadata)
    new_files = filter_new_files(available_files, loaded_file_keys)
    skipped_files = len(available_files) - len(new_files)

    logger.info(
        "Incremental selection complete: %s new file(s), %s skipped file(s)",
        len(new_files),
        skipped_files,
    )

    if not new_files:
        logger.info("No new files to ingest. Pipeline outputs remain unchanged.")
        current_business_data = read_business_data(ingestion_output_paths["business_data"])
        ingestion_output_paths_result = ingestion_output_paths
        rows_ingested = 0
    else:
        ingestion_result = load_sales_files(new_files)
        merged_result = IngestionResult(
            data=merge_business_data(ingestion_output_paths["business_data"], ingestion_result.data),
            file_inventory=merge_ingestion_metadata(
                existing_metadata,
                ingestion_result.file_inventory,
            ),
        )
        ingestion_output_paths_result = save_ingestion_outputs(merged_result, ingestion_output_dir)
        current_business_data = merged_result.data
        rows_ingested = len(ingestion_result.data)
        logger.info(
            "Ingestion stage completed: %s new file(s) processed, %s row(s) ingested",
            len(new_files),
            rows_ingested,
        )

    logger.info("Starting transformation stage on %s row(s)", len(current_business_data))
    cleaning_result = clean_sales_data(current_business_data)
    transformation_output_paths = save_transformation_outputs(
        cleaning_result,
        transformation_output_dir,
    )
    logger.info(
        "Transformation stage completed: %s cleaned row(s) written",
        len(cleaning_result.data),
    )
    combined_output_paths = {
        **ingestion_output_paths_result,
        **transformation_output_paths,
    }
    logger.info("Pipeline run completed successfully")
    return PipelineRunResult(
        output_paths=combined_output_paths,
        new_files_processed=len(new_files),
        skipped_files=skipped_files,
        rows_ingested=rows_ingested,
        rows_cleaned=len(cleaning_result.data),
    )
