from dataclasses import dataclass
import logging
from pathlib import Path

import pandas as pd

from .analytic.kpis import (
    KPIBundle,
    build_kpi_bundle,
    merge_dimension_kpis,
    merge_monthly_kpis,
    merge_overview_kpis,
    merge_quality_reports,
)
from .logging_config import configure_logging
from .reporting.excel_report import create_management_report
from .transformation.cleaning import clean_sales_data

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
    rows_analyzed: int


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


def get_analytics_output_paths(output_dir: Path) -> dict[str, Path]:
    """Return the CSV output paths for the analytics step."""
    return {
        "kpi_overview": output_dir / "kpi_overview.csv",
        "monthly_kpis": output_dir / "monthly_kpis.csv",
        "kpis_by_store": output_dir / "kpis_by_store.csv",
        "kpis_by_plan": output_dir / "kpis_by_plan.csv",
        "analytics_quality": output_dir / "analytics_quality.csv",
        "analytics_file_inventory": output_dir / "analytics_file_inventory.csv",
    }


def get_reporting_output_dir(output_root_dir: Path) -> Path:
    """Return the output directory for stakeholder Excel reports."""
    return output_root_dir / "reports"


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


def read_clean_sales_data(clean_data_path: Path) -> pd.DataFrame:
    """Load the cleaned sales data CSV if it exists."""
    if not clean_data_path.exists():
        return pd.DataFrame()

    logger.info("Loading cleaned sales data from %s", clean_data_path)
    return pd.read_csv(clean_data_path)


def read_csv_output(output_path: Path, output_label: str) -> pd.DataFrame:
    """Load a CSV output file if it exists."""
    if not output_path.exists():
        return pd.DataFrame()

    logger.info("Loading %s from %s", output_label, output_path)
    return pd.read_csv(output_path)


def load_analytics_bundle(output_paths: dict[str, Path]) -> KPIBundle:
    """Load the current analytics outputs from disk."""
    return KPIBundle(
        overview=read_csv_output(output_paths["kpi_overview"], "KPI overview"),
        monthly=read_csv_output(output_paths["monthly_kpis"], "monthly KPIs"),
        by_store=read_csv_output(output_paths["kpis_by_store"], "store KPIs"),
        by_plan=read_csv_output(output_paths["kpis_by_plan"], "plan KPIs"),
        quality=read_csv_output(output_paths["analytics_quality"], "analytics quality report"),
        file_inventory=read_csv_output(
            output_paths["analytics_file_inventory"],
            "analytics file inventory",
        ),
    )


def get_file_keys_from_clean_data(clean_data: pd.DataFrame) -> set[tuple[str, str]]:
    """Return the set of source files already present in the clean output."""
    if clean_data.empty:
        return set()

    required_columns = {"source_folder", "source_file"}
    if not required_columns.issubset(clean_data.columns):
        return set()

    source_folders = clean_data["source_folder"].fillna("").astype(str)
    source_files = clean_data["source_file"].fillna("").astype(str)
    return set(zip(source_folders, source_files))


def filter_rows_for_file_keys(
    data: pd.DataFrame,
    file_keys: set[tuple[str, str]],
) -> pd.DataFrame:
    """Return only the rows whose source file belongs to the given file keys."""
    if data.empty or not file_keys:
        return data.iloc[0:0].copy()

    file_key_series = list(
        zip(
            data["source_folder"].fillna("").astype(str),
            data["source_file"].fillna("").astype(str),
        )
    )
    mask = pd.Series(
        [file_key in file_keys for file_key in file_key_series],
        index=data.index,
    )
    return data[mask].copy()


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
    clean_data: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Save transformation outputs to CSV files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = get_transformation_output_paths(output_dir)

    logger.info("Writing clean sales data to %s", output_paths["clean_sales_data"])
    clean_data.to_csv(output_paths["clean_sales_data"], index=False)

    return output_paths


def save_analytics_outputs(
    kpi_bundle: KPIBundle,
    output_dir: Path,
) -> dict[str, Path]:
    """Save analytics outputs to CSV files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = get_analytics_output_paths(output_dir)

    logger.info("Writing KPI overview to %s", output_paths["kpi_overview"])
    kpi_bundle.overview.to_csv(output_paths["kpi_overview"], index=False)
    logger.info("Writing monthly KPIs to %s", output_paths["monthly_kpis"])
    kpi_bundle.monthly.to_csv(output_paths["monthly_kpis"], index=False)
    logger.info("Writing store KPIs to %s", output_paths["kpis_by_store"])
    kpi_bundle.by_store.to_csv(output_paths["kpis_by_store"], index=False)
    logger.info("Writing plan KPIs to %s", output_paths["kpis_by_plan"])
    kpi_bundle.by_plan.to_csv(output_paths["kpis_by_plan"], index=False)
    logger.info("Writing analytics quality report to %s", output_paths["analytics_quality"])
    kpi_bundle.quality.to_csv(output_paths["analytics_quality"], index=False)
    logger.info(
        "Writing analytics file inventory to %s",
        output_paths["analytics_file_inventory"],
    )
    kpi_bundle.file_inventory.to_csv(output_paths["analytics_file_inventory"], index=False)

    return output_paths


def merge_clean_sales_data(
    clean_data_path: Path,
    new_clean_data: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Append only unseen cleaned transactions to the existing clean output."""
    if not clean_data_path.exists():
        logger.info("No existing clean sales data found at %s", clean_data_path)
        return new_clean_data, 0

    existing_clean_data = read_clean_sales_data(clean_data_path)
    if new_clean_data.empty:
        return existing_clean_data, 0

    existing_transaction_ids = set(
        existing_clean_data["transaction_id"].astype("string").dropna()
    )
    filtered_new_clean_data = new_clean_data[
        ~new_clean_data["transaction_id"].astype("string").isin(existing_transaction_ids)
    ].copy()
    skipped_duplicates = len(new_clean_data) - len(filtered_new_clean_data)

    if skipped_duplicates:
        logger.info(
            "Skipped %s cleaned row(s) already present in clean_sales_data.csv",
            skipped_duplicates,
        )

    if filtered_new_clean_data.empty:
        return existing_clean_data, skipped_duplicates

    merged_clean_data = pd.concat(
        [existing_clean_data, filtered_new_clean_data],
        ignore_index=True,
    )
    merged_clean_data = merged_clean_data.sort_values(
        ["transaction_date", "transaction_id"]
    ).reset_index(drop=True)
    return merged_clean_data, skipped_duplicates


def run_pipeline(
    output_dir: Path | None = None,
    source_dir: Path | None = None,
) -> PipelineRunResult:
    """Run the current pipeline and return the generated file paths."""
    log_file = configure_logging()
    ingestion_output_dir = output_dir or get_project_root() / "outputs" / "ingestion"
    output_root_dir = ingestion_output_dir.parent
    transformation_output_dir = output_root_dir / "transformation"
    analytics_output_dir = output_root_dir / "analytics"
    reporting_output_dir = get_reporting_output_dir(output_root_dir)
    ingestion_output_paths = get_output_paths(ingestion_output_dir)
    transformation_output_paths = get_transformation_output_paths(transformation_output_dir)
    analytics_output_paths = get_analytics_output_paths(analytics_output_dir)
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
        logger.info("No new files to ingest.")
        current_business_data = read_business_data(ingestion_output_paths["business_data"])
        current_ingestion_metadata = existing_metadata
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
        current_ingestion_metadata = merged_result.file_inventory
        rows_ingested = len(ingestion_result.data)
        logger.info(
            "Ingestion stage completed: %s new file(s) processed, %s row(s) ingested",
            len(new_files),
            rows_ingested,
        )

    existing_clean_data = read_clean_sales_data(transformation_output_paths["clean_sales_data"])
    transformed_file_keys = get_file_keys_from_clean_data(existing_clean_data)
    loaded_file_keys = get_loaded_file_keys(current_ingestion_metadata)
    pending_transformation_keys = loaded_file_keys - transformed_file_keys

    logger.info(
        "Transformation selection complete: %s file(s) pending transformation",
        len(pending_transformation_keys),
    )

    if not pending_transformation_keys:
        logger.info("No pending files to transform. Transformation stage skipped.")
        current_clean_data = existing_clean_data
        transformation_output_paths_result = transformation_output_paths
        rows_cleaned = 0
    else:
        raw_rows_to_transform = filter_rows_for_file_keys(
            current_business_data,
            pending_transformation_keys,
        )
        logger.info(
            "Starting transformation stage on %s raw row(s) from %s file(s)",
            len(raw_rows_to_transform),
            len(pending_transformation_keys),
        )
        cleaning_result = clean_sales_data(raw_rows_to_transform)
        merged_clean_data, skipped_clean_duplicates = merge_clean_sales_data(
            transformation_output_paths["clean_sales_data"],
            cleaning_result.data,
        )
        transformation_output_paths_result = save_transformation_outputs(
            merged_clean_data,
            transformation_output_dir,
        )
        rows_cleaned = len(cleaning_result.data) - skipped_clean_duplicates
        current_clean_data = merged_clean_data
        logger.info(
            "Transformation stage completed: %s cleaned row(s) appended, %s duplicate row(s) skipped",
            rows_cleaned,
            skipped_clean_duplicates,
        )

    existing_analytics_inventory = read_csv_output(
        analytics_output_paths["analytics_file_inventory"],
        "analytics file inventory",
    )
    analytics_loaded_file_keys = get_loaded_file_keys(existing_analytics_inventory)
    clean_file_keys = get_file_keys_from_clean_data(current_clean_data)
    pending_analytics_keys = clean_file_keys - analytics_loaded_file_keys

    logger.info(
        "Analytics selection complete: %s file(s) pending KPI processing",
        len(pending_analytics_keys),
    )

    if not pending_analytics_keys:
        logger.info("No pending files to analyze. Analytics stage skipped.")
        current_kpi_bundle = load_analytics_bundle(analytics_output_paths)
        analytics_output_paths_result = analytics_output_paths
        rows_analyzed = 0
    else:
        analytics_input_data = filter_rows_for_file_keys(
            current_clean_data,
            pending_analytics_keys,
        )
        logger.info(
            "Starting analytics stage on %s cleaned row(s) from %s file(s)",
            len(analytics_input_data),
            len(pending_analytics_keys),
        )
        kpi_bundle = build_kpi_bundle(analytics_input_data)

        existing_overview = read_csv_output(analytics_output_paths["kpi_overview"], "KPI overview")
        existing_monthly = read_csv_output(analytics_output_paths["monthly_kpis"], "monthly KPIs")
        existing_by_store = read_csv_output(analytics_output_paths["kpis_by_store"], "store KPIs")
        existing_by_plan = read_csv_output(analytics_output_paths["kpis_by_plan"], "plan KPIs")
        existing_quality = read_csv_output(
            analytics_output_paths["analytics_quality"],
            "analytics quality report",
        )

        merged_monthly = merge_monthly_kpis(existing_monthly, kpi_bundle.monthly)
        merged_by_store = merge_dimension_kpis(existing_by_store, kpi_bundle.by_store, "store")
        merged_by_plan = merge_dimension_kpis(existing_by_plan, kpi_bundle.by_plan, "plan")
        merged_overview = merge_overview_kpis(
            existing_overview,
            merged_monthly,
            merged_by_store,
            analytics_input_data,
        )

        quality_batch = kpi_bundle.quality.copy()
        quality_batch["run_timestamp"] = pd.Timestamp.utcnow().isoformat()
        merged_quality = merge_quality_reports(existing_quality, quality_batch)
        merged_analytics_inventory = merge_ingestion_metadata(
            existing_analytics_inventory,
            kpi_bundle.file_inventory,
        )

        current_kpi_bundle = KPIBundle(
            overview=merged_overview,
            monthly=merged_monthly,
            by_store=merged_by_store,
            by_plan=merged_by_plan,
            quality=merged_quality,
            file_inventory=merged_analytics_inventory,
        )
        analytics_output_paths_result = save_analytics_outputs(
            current_kpi_bundle,
            analytics_output_dir,
        )
        rows_analyzed = len(analytics_input_data)
        logger.info(
            "Analytics stage completed: %s cleaned row(s) processed into KPI outputs",
            rows_analyzed,
        )

    report_result = create_management_report(
        output_dir=reporting_output_dir,
        kpis=current_kpi_bundle,
    )
    if report_result.generated:
        logger.info(
            "Reporting stage completed: %s generated for latest month %s",
            report_result.path,
            report_result.latest_month or "n/a",
        )
    else:
        logger.info(
            "Reporting stage skipped: existing report reused at %s for latest month %s",
            report_result.path,
            report_result.latest_month or "n/a",
        )

    combined_output_paths = {
        **ingestion_output_paths_result,
        **transformation_output_paths_result,
        **analytics_output_paths_result,
        "management_report": report_result.path,
    }
    logger.info("Pipeline run completed successfully")
    return PipelineRunResult(
        output_paths=combined_output_paths,
        new_files_processed=len(new_files),
        skipped_files=skipped_files,
        rows_ingested=rows_ingested,
        rows_cleaned=rows_cleaned,
        rows_analyzed=rows_analyzed,
    )
