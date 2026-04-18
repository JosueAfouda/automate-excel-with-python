"""Clean and standardize raw sales transactions."""

from dataclasses import dataclass
import logging

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "transaction_id",
    "store",
    "transaction_date",
    "plan",
    "contract_type",
    "amount",
    "status",
    "source_file",
    "source_folder",
]


@dataclass
class CleaningResult:
    data: pd.DataFrame
    quality_report: pd.DataFrame


def validate_cleaning_input(raw_df: pd.DataFrame) -> None:
    """Ensure the cleaning input contains the expected columns."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in raw_df.columns
    ]
    if missing_columns:
        raise ValueError(
            "The cleaning step is missing required columns: "
            + ", ".join(missing_columns)
        )


def clean_sales_data(raw_df: pd.DataFrame) -> CleaningResult:
    """Apply business cleaning rules to the ingested sales data."""
    validate_cleaning_input(raw_df)

    df = raw_df.copy()
    quality_rows: list[dict[str, object]] = [{"stage": "raw_rows", "rows": len(df)}]
    logger.info("Starting data cleaning on %s row(s)", len(df))

    df["transaction_id"] = df["transaction_id"].astype("string").str.strip()
    df = df[
        df["transaction_id"].notna()
        & (df["transaction_id"] != "")
        & (df["transaction_id"].str.lower() != "nan")
    ]
    quality_rows.append({"stage": "after_transaction_id_filter", "rows": len(df)})
    logger.info("Rows after transaction_id filter: %s", len(df))

    df["status"] = df["status"].fillna("ACTIVE").astype("string").str.upper().str.strip()
    df["store"] = df["store"].astype("string").str.strip()
    df["plan"] = df["plan"].astype("string").str.strip().str.title()
    df["contract_type"] = (
        df["contract_type"].astype("string").str.upper().str.strip()
    )
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce",
        format="mixed",
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = df[df["transaction_date"].notna()]
    df = df[df["amount"].notna() & (df["amount"] > 0)]
    quality_rows.append({"stage": "after_type_and_amount_filter", "rows": len(df)})
    logger.info("Rows after date/amount filters: %s", len(df))

    df = df[df["status"] == "ACTIVE"]
    quality_rows.append({"stage": "after_status_filter", "rows": len(df)})
    logger.info("Rows after ACTIVE status filter: %s", len(df))

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    quality_rows.append(
        {
            "stage": "after_dedup",
            "rows": len(df),
            "rows_removed": before_dedup - len(df),
        }
    )
    logger.info(
        "Rows after deduplication: %s (removed %s duplicate row(s))",
        len(df),
        before_dedup - len(df),
    )

    df["month_start"] = df["transaction_date"].dt.to_period("M").dt.to_timestamp()
    df["year_month"] = df["month_start"].dt.strftime("%Y-%m")
    df = df.sort_values(["transaction_date", "transaction_id"]).reset_index(drop=True)

    quality_report = pd.DataFrame(quality_rows)
    logger.info("Data cleaning completed with %s cleaned row(s)", len(df))
    return CleaningResult(data=df, quality_report=quality_report)
