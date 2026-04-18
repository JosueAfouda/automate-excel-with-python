"""Business KPI computation for monthly sales reporting."""

from __future__ import annotations

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
    "source_file",
    "source_folder",
    "month_start",
    "year_month",
]
OVERVIEW_METRICS = [
    "period_start",
    "period_end",
    "total_revenue",
    "total_transactions",
    "average_ticket",
    "new_revenue",
    "existing_revenue",
    "new_revenue_share",
    "stores_count",
]


@dataclass
class KPIBundle:
    overview: pd.DataFrame
    monthly: pd.DataFrame
    by_store: pd.DataFrame
    by_plan: pd.DataFrame
    quality: pd.DataFrame
    file_inventory: pd.DataFrame


def validate_kpi_input(cleaned_df: pd.DataFrame) -> None:
    """Ensure the KPI input contains the expected columns."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in cleaned_df.columns
    ]
    if missing_columns:
        raise ValueError(
            "The KPI step is missing required columns: " + ", ".join(missing_columns)
        )


def normalize_kpi_input(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize cleaned sales data before KPI aggregation."""
    validate_kpi_input(cleaned_df)

    df = cleaned_df.copy()
    df["transaction_id"] = df["transaction_id"].astype("string").str.strip()
    df["store"] = df["store"].astype("string").str.strip()
    df["plan"] = df["plan"].astype("string").str.strip().str.title()
    df["contract_type"] = df["contract_type"].astype("string").str.upper().str.strip()
    df["source_file"] = df["source_file"].astype("string").str.strip()
    df["source_folder"] = df["source_folder"].astype("string").str.strip()
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce",
        format="mixed",
    )
    df["month_start"] = pd.to_datetime(
        df["month_start"],
        errors="coerce",
        format="mixed",
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    invalid_mask = (
        df["transaction_id"].isna()
        | df["transaction_date"].isna()
        | df["month_start"].isna()
        | df["amount"].isna()
    )
    if invalid_mask.any():
        raise ValueError(
            "The KPI step received invalid cleaned rows after normalization."
        )

    return df


def _build_overview(df: pd.DataFrame) -> pd.DataFrame:
    total_revenue = float(df["amount"].sum())
    total_transactions = int(df["transaction_id"].nunique())
    average_ticket = total_revenue / total_transactions if total_transactions else 0.0
    new_revenue = float(df.loc[df["contract_type"] == "NEW", "amount"].sum())
    existing_revenue = float(
        df.loc[df["contract_type"] == "EXISTING", "amount"].sum()
    )
    new_share = new_revenue / total_revenue if total_revenue else 0.0

    rows = [
        {"metric": "period_start", "value": df["transaction_date"].min().date().isoformat()},
        {"metric": "period_end", "value": df["transaction_date"].max().date().isoformat()},
        {"metric": "total_revenue", "value": total_revenue},
        {"metric": "total_transactions", "value": total_transactions},
        {"metric": "average_ticket", "value": average_ticket},
        {"metric": "new_revenue", "value": new_revenue},
        {"metric": "existing_revenue", "value": existing_revenue},
        {"metric": "new_revenue_share", "value": new_share},
        {"metric": "stores_count", "value": int(df["store"].nunique())},
    ]
    return pd.DataFrame(rows)


def _build_monthly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    revenue_by_contract = (
        df.groupby(["month_start", "contract_type"], as_index=False)["amount"]
        .sum()
        .pivot(index="month_start", columns="contract_type", values="amount")
    )
    revenue_by_contract = revenue_by_contract.rename(
        columns={"EXISTING": "revenue_existing", "NEW": "revenue_new"}
    )
    revenue_by_contract = revenue_by_contract.fillna(0.0).reset_index()

    transactions = (
        df.groupby("month_start", as_index=False)
        .agg(transactions=("transaction_id", "nunique"))
    )

    monthly = revenue_by_contract.merge(transactions, on="month_start", how="left")
    monthly["revenue_existing"] = monthly.get("revenue_existing", 0.0)
    monthly["revenue_new"] = monthly.get("revenue_new", 0.0)
    monthly["revenue_total"] = monthly["revenue_existing"] + monthly["revenue_new"]
    monthly["average_ticket"] = monthly["revenue_total"] / monthly["transactions"]
    monthly = monthly.sort_values("month_start").reset_index(drop=True)
    monthly["growth_mom"] = monthly["revenue_total"].pct_change().fillna(0.0)
    monthly["year_month"] = monthly["month_start"].dt.strftime("%Y-%m")
    return monthly[
        [
            "year_month",
            "month_start",
            "revenue_existing",
            "revenue_new",
            "revenue_total",
            "transactions",
            "average_ticket",
            "growth_mom",
        ]
    ]


def _build_store_kpis(df: pd.DataFrame) -> pd.DataFrame:
    by_store = (
        df.groupby("store", as_index=False)
        .agg(revenue=("amount", "sum"), transactions=("transaction_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    by_store["average_ticket"] = by_store["revenue"] / by_store["transactions"]
    by_store["revenue_share"] = by_store["revenue"] / by_store["revenue"].sum()
    return by_store


def _build_plan_kpis(df: pd.DataFrame) -> pd.DataFrame:
    by_plan = (
        df.groupby("plan", as_index=False)
        .agg(revenue=("amount", "sum"), transactions=("transaction_id", "nunique"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    by_plan["average_ticket"] = by_plan["revenue"] / by_plan["transactions"]
    by_plan["revenue_share"] = by_plan["revenue"] / by_plan["revenue"].sum()
    return by_plan


def _build_quality_report(
    df: pd.DataFrame,
    monthly: pd.DataFrame,
    by_store: pd.DataFrame,
    by_plan: pd.DataFrame,
) -> pd.DataFrame:
    """Build a batch-level quality report for the KPI stage."""
    return pd.DataFrame(
        [
            {
                "clean_rows_input": len(df),
                "source_files_processed": int(df["source_file"].nunique()),
                "months_covered": int(df["year_month"].nunique()),
                "monthly_rows_output": len(monthly),
                "store_rows_output": len(by_store),
                "plan_rows_output": len(by_plan),
                "period_start": df["transaction_date"].min().date().isoformat(),
                "period_end": df["transaction_date"].max().date().isoformat(),
            }
        ]
    )


def _build_file_inventory(df: pd.DataFrame) -> pd.DataFrame:
    """Build the analytics file inventory for the current batch."""
    file_inventory = (
        df.groupby(["source_folder", "source_file"], as_index=False)
        .agg(
            rows_processed=("transaction_id", "count"),
            period_start=("transaction_date", "min"),
            period_end=("transaction_date", "max"),
        )
        .sort_values(["source_folder", "source_file"])
        .reset_index(drop=True)
    )
    file_inventory["period_start"] = file_inventory["period_start"].dt.date.astype(str)
    file_inventory["period_end"] = file_inventory["period_end"].dt.date.astype(str)
    file_inventory["status"] = "loaded"
    return file_inventory


def build_kpi_bundle(cleaned_df: pd.DataFrame) -> KPIBundle:
    """Build all KPI outputs for a cleaned batch of sales data."""
    df = normalize_kpi_input(cleaned_df)
    logger.info("Building KPI bundle for %s cleaned row(s)", len(df))

    overview = _build_overview(df)
    monthly = _build_monthly_kpis(df)
    by_store = _build_store_kpis(df)
    by_plan = _build_plan_kpis(df)
    quality = _build_quality_report(df, monthly, by_store, by_plan)
    file_inventory = _build_file_inventory(df)

    logger.info(
        "KPI bundle built: %s month row(s), %s store row(s), %s plan row(s)",
        len(monthly),
        len(by_store),
        len(by_plan),
    )
    return KPIBundle(
        overview=overview,
        monthly=monthly,
        by_store=by_store,
        by_plan=by_plan,
        quality=quality,
        file_inventory=file_inventory,
    )


def normalize_monthly_kpis(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize a monthly KPI table loaded from CSV."""
    if monthly_df.empty:
        return pd.DataFrame(
            columns=[
                "year_month",
                "month_start",
                "revenue_existing",
                "revenue_new",
                "revenue_total",
                "transactions",
                "average_ticket",
                "growth_mom",
            ]
        )

    normalized = monthly_df.copy()
    normalized["month_start"] = pd.to_datetime(
        normalized["month_start"],
        errors="coerce",
        format="mixed",
    )
    for column in ["revenue_existing", "revenue_new", "transactions"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0.0)
    normalized["year_month"] = normalized["month_start"].dt.strftime("%Y-%m")
    normalized["revenue_total"] = normalized["revenue_existing"] + normalized["revenue_new"]
    normalized["average_ticket"] = normalized["revenue_total"] / normalized["transactions"].replace(0, pd.NA)
    normalized["average_ticket"] = normalized["average_ticket"].fillna(0.0)
    normalized = normalized.sort_values("month_start").reset_index(drop=True)
    normalized["growth_mom"] = normalized["revenue_total"].pct_change().fillna(0.0)
    return normalized


def merge_monthly_kpis(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Incrementally merge monthly KPI deltas into the historical table."""
    existing_base = normalize_monthly_kpis(existing_df)[
        ["year_month", "month_start", "revenue_existing", "revenue_new", "transactions"]
    ]
    new_base = normalize_monthly_kpis(new_df)[
        ["year_month", "month_start", "revenue_existing", "revenue_new", "transactions"]
    ]
    combined = pd.concat([existing_base, new_base], ignore_index=True)
    if combined.empty:
        return normalize_monthly_kpis(combined)

    aggregated = (
        combined.groupby(["year_month", "month_start"], as_index=False)
        .agg(
            revenue_existing=("revenue_existing", "sum"),
            revenue_new=("revenue_new", "sum"),
            transactions=("transactions", "sum"),
        )
        .sort_values("month_start")
        .reset_index(drop=True)
    )
    aggregated["revenue_total"] = aggregated["revenue_existing"] + aggregated["revenue_new"]
    aggregated["average_ticket"] = (
        aggregated["revenue_total"] / aggregated["transactions"].replace(0, pd.NA)
    ).fillna(0.0)
    aggregated["growth_mom"] = aggregated["revenue_total"].pct_change().fillna(0.0)
    return aggregated


def normalize_dimension_kpis(
    dimension_df: pd.DataFrame,
    key_column: str,
) -> pd.DataFrame:
    """Normalize a dimensional KPI table loaded from CSV."""
    if dimension_df.empty:
        return pd.DataFrame(
            columns=[key_column, "revenue", "transactions", "average_ticket", "revenue_share"]
        )

    normalized = dimension_df.copy()
    normalized[key_column] = normalized[key_column].astype("string").str.strip()
    for column in ["revenue", "transactions"]:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0.0)
    normalized = normalized[[key_column, "revenue", "transactions"]]
    normalized = normalized.groupby(key_column, as_index=False).agg(
        revenue=("revenue", "sum"),
        transactions=("transactions", "sum"),
    )
    normalized = normalized.sort_values("revenue", ascending=False).reset_index(drop=True)
    normalized["average_ticket"] = (
        normalized["revenue"] / normalized["transactions"].replace(0, pd.NA)
    ).fillna(0.0)
    total_revenue = normalized["revenue"].sum()
    normalized["revenue_share"] = (
        normalized["revenue"] / total_revenue if total_revenue else 0.0
    )
    return normalized


def merge_dimension_kpis(
    existing_df: pd.DataFrame,
    new_df: pd.DataFrame,
    key_column: str,
) -> pd.DataFrame:
    """Incrementally merge dimensional KPI deltas into the historical table."""
    existing_base = normalize_dimension_kpis(existing_df, key_column)[
        [key_column, "revenue", "transactions"]
    ]
    new_base = normalize_dimension_kpis(new_df, key_column)[
        [key_column, "revenue", "transactions"]
    ]
    combined = pd.concat([existing_base, new_base], ignore_index=True)
    return normalize_dimension_kpis(combined, key_column)


def merge_overview_kpis(
    existing_overview: pd.DataFrame,
    monthly_df: pd.DataFrame,
    by_store_df: pd.DataFrame,
    new_cleaned_df: pd.DataFrame,
) -> pd.DataFrame:
    """Incrementally update the overview KPI table."""
    existing_metrics: dict[str, str] = {}
    if not existing_overview.empty:
        existing_metrics = {
            str(row["metric"]): str(row["value"])
            for _, row in existing_overview.iterrows()
        }

    total_revenue = float(monthly_df["revenue_total"].sum()) if not monthly_df.empty else 0.0
    total_transactions = int(by_store_df["transactions"].sum()) if not by_store_df.empty else 0
    average_ticket = total_revenue / total_transactions if total_transactions else 0.0
    new_revenue = float(monthly_df["revenue_new"].sum()) if not monthly_df.empty else 0.0
    existing_revenue = (
        float(monthly_df["revenue_existing"].sum()) if not monthly_df.empty else 0.0
    )
    new_share = new_revenue / total_revenue if total_revenue else 0.0
    stores_count = int(len(by_store_df))

    new_period_start = pd.to_datetime(
        new_cleaned_df["transaction_date"],
        errors="coerce",
        format="mixed",
    ).min()
    new_period_end = pd.to_datetime(
        new_cleaned_df["transaction_date"],
        errors="coerce",
        format="mixed",
    ).max()

    existing_period_start = pd.to_datetime(existing_metrics.get("period_start"), errors="coerce")
    existing_period_end = pd.to_datetime(existing_metrics.get("period_end"), errors="coerce")

    period_start_candidates = [value for value in [existing_period_start, new_period_start] if pd.notna(value)]
    period_end_candidates = [value for value in [existing_period_end, new_period_end] if pd.notna(value)]

    rows = [
        {
            "metric": "period_start",
            "value": min(period_start_candidates).date().isoformat() if period_start_candidates else "",
        },
        {
            "metric": "period_end",
            "value": max(period_end_candidates).date().isoformat() if period_end_candidates else "",
        },
        {"metric": "total_revenue", "value": total_revenue},
        {"metric": "total_transactions", "value": total_transactions},
        {"metric": "average_ticket", "value": average_ticket},
        {"metric": "new_revenue", "value": new_revenue},
        {"metric": "existing_revenue", "value": existing_revenue},
        {"metric": "new_revenue_share", "value": new_share},
        {"metric": "stores_count", "value": stores_count},
    ]
    return pd.DataFrame(rows)


def merge_quality_reports(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
    """Append analytics quality reports over time."""
    if existing_df.empty:
        return new_df.copy()
    if new_df.empty:
        return existing_df.copy()
    return pd.concat([existing_df, new_df], ignore_index=True, sort=False)
