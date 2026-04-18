from pathlib import Path

from .ingestion.sales_ingestion import IngestionResult, load_sales_data


def get_project_root() -> Path:
    """Return the root folder of the project."""
    return Path(__file__).resolve().parents[1]


def save_ingestion_outputs(
    ingestion_result: IngestionResult,
    output_dir: Path,
) -> dict[str, Path]:
    """Save ingestion outputs to CSV files and return their paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    business_data_path = output_dir / "business_data.csv"
    ingestion_metadata_path = output_dir / "ingestion_metadata.csv"

    ingestion_result.data.to_csv(business_data_path, index=False)
    ingestion_result.file_inventory.to_csv(ingestion_metadata_path, index=False)

    return {
        "business_data": business_data_path,
        "ingestion_metadata": ingestion_metadata_path,
    }


def run_pipeline(output_dir: Path | None = None) -> dict[str, Path]:
    """Run the current pipeline and return the generated file paths."""
    target_output_dir = output_dir or get_project_root() / "outputs" / "ingestion"

    ingestion_result = load_sales_data()
    return save_ingestion_outputs(ingestion_result, target_output_dir)
