"""Generate the final management report in Excel."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from xlsxwriter.format import Format
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from ..analytic.kpis import KPIBundle, normalize_dimension_kpis, normalize_monthly_kpis

SUMMARY_LABELS = {
    "period_start": "Debut de periode",
    "period_end": "Fin de periode",
    "total_revenue": "Chiffre d'affaires total",
    "total_transactions": "Transactions",
    "average_ticket": "Panier moyen",
    "new_revenue": "CA nouveaux contrats",
    "existing_revenue": "CA contrats existants",
    "new_revenue_share": "Part nouveaux contrats",
    "stores_count": "Magasins actifs",
}
SUMMARY_ORDER = [
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
CURRENCY_COLUMNS = {
    "value",
    "revenue_existing",
    "revenue_new",
    "revenue_total",
    "revenue",
    "average_ticket",
}
INTEGER_COLUMNS = {"transactions"}
PERCENT_COLUMNS = {"growth_mom", "revenue_share"}
DATE_COLUMNS = {"month_start"}


@dataclass(frozen=True)
class ReportFormats:
    """Workbook formats used across the report."""

    title: Format
    metadata_label: Format
    metadata_value: Format
    header: Format
    text: Format
    date: Format
    currency: Format
    integer: Format
    percent: Format


def build_report_output_path(
    output_dir: Path,
    generated_at: pd.Timestamp | None = None,
) -> Path:
    """Return a unique timestamped output path for the management report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_timestamp = (generated_at or pd.Timestamp.now()).strftime("%Y%m%d_%H%M%S")
    candidate_path = output_dir / f"rapport_ventes_{report_timestamp}.xlsx"
    suffix = 1

    while candidate_path.exists():
        candidate_path = output_dir / f"rapport_ventes_{report_timestamp}_{suffix:02d}.xlsx"
        suffix += 1

    return candidate_path


def _build_report_formats(workbook: Workbook) -> ReportFormats:
    """Create and return the workbook formats used in the report."""
    return ReportFormats(
        title=workbook.add_format(
            {
                "bold": True,
                "font_size": 16,
                "font_name": "Calibri",
                "font_color": "#1F1F1F",
            }
        ),
        metadata_label=workbook.add_format(
            {
                "bold": True,
                "font_name": "Calibri",
                "font_size": 11,
                "font_color": "#44546A",
            }
        ),
        metadata_value=workbook.add_format({"font_name": "Calibri", "font_size": 11}),
        header=workbook.add_format(
            {
                "bold": True,
                "bg_color": "#D9E2F3",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "font_name": "Calibri",
                "font_size": 11,
            }
        ),
        text=workbook.add_format({"font_name": "Calibri", "font_size": 11}),
        date=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "num_format": "yyyy-mm-dd"}
        ),
        currency=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "num_format": "$#,##0.00"}
        ),
        integer=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "num_format": "#,##0"}
        ),
        percent=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "num_format": "0.0%"}
        ),
    )


def _parse_overview_value(metric_name: str, raw_value: object) -> object:
    """Convert overview values to their reporting-friendly Python types."""
    if metric_name in {"period_start", "period_end"}:
        timestamp = pd.to_datetime(raw_value, errors="coerce")
        return timestamp.to_pydatetime() if pd.notna(timestamp) else str(raw_value)

    if metric_name in {
        "total_revenue",
        "average_ticket",
        "new_revenue",
        "existing_revenue",
        "new_revenue_share",
        "total_transactions",
        "stores_count",
    }:
        numeric_value = pd.to_numeric(raw_value, errors="coerce")
        return float(numeric_value) if pd.notna(numeric_value) else 0.0

    return raw_value


def _normalize_overview(overview_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize the overview KPI table before writing it to Excel."""
    if overview_df.empty:
        return pd.DataFrame(columns=["metric", "value"])

    normalized = overview_df.copy()
    normalized["metric"] = normalized["metric"].astype("string").str.strip()
    normalized["value"] = [
        _parse_overview_value(str(metric_name), raw_value)
        for metric_name, raw_value in zip(normalized["metric"], normalized["value"])
    ]
    return normalized


def _normalize_report_bundle(kpis: KPIBundle) -> KPIBundle:
    """Normalize KPI outputs so formatting works whether data comes from memory or CSV."""
    return KPIBundle(
        overview=_normalize_overview(kpis.overview),
        monthly=normalize_monthly_kpis(kpis.monthly),
        by_store=normalize_dimension_kpis(kpis.by_store, "store"),
        by_plan=normalize_dimension_kpis(kpis.by_plan, "plan"),
        quality=kpis.quality.copy(),
        file_inventory=kpis.file_inventory.copy(),
    )


def _estimate_column_width(dataframe: pd.DataFrame, column_name: str) -> int:
    """Estimate a reasonable Excel width for a dataframe column."""
    series = dataframe[column_name] if column_name in dataframe.columns else pd.Series(dtype="object")
    sample_lengths = series.head(250).fillna("").astype(str).map(len)
    max_length = max([len(str(column_name)), *sample_lengths.tolist()], default=len(str(column_name)))
    return min(max_length + 2, 28)


def _get_column_format(
    column_name: str,
    formats: ReportFormats,
) -> Format:
    """Return the Excel format to use for a dataframe column."""
    if column_name in DATE_COLUMNS:
        return formats.date
    if column_name in CURRENCY_COLUMNS:
        return formats.currency
    if column_name in INTEGER_COLUMNS:
        return formats.integer
    if column_name in PERCENT_COLUMNS:
        return formats.percent
    return formats.text


def _apply_dataframe_layout(
    worksheet: Worksheet,
    dataframe: pd.DataFrame,
    formats: ReportFormats,
) -> None:
    """Apply headers, filters, widths, and freeze panes to a dataframe sheet."""
    worksheet.hide_gridlines(2)
    worksheet.freeze_panes(1, 0)

    if dataframe.columns.empty:
        return

    worksheet.autofilter(0, 0, max(len(dataframe), 1), len(dataframe.columns) - 1)
    for column_index, column_name in enumerate(dataframe.columns):
        worksheet.write(0, column_index, column_name, formats.header)
        worksheet.set_column(
            column_index,
            column_index,
            _estimate_column_width(dataframe, str(column_name)),
            _get_column_format(str(column_name), formats),
        )


def _write_dataframe_sheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    dataframe: pd.DataFrame,
    formats: ReportFormats,
) -> Worksheet:
    """Write a dataframe sheet and apply workbook formatting."""
    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    _apply_dataframe_layout(worksheet, dataframe, formats)
    return worksheet


def _get_summary_format(metric_name: str, formats: ReportFormats) -> Format:
    """Return the appropriate format for a summary metric row."""
    if metric_name in {"period_start", "period_end"}:
        return formats.date
    if metric_name in {"total_transactions", "stores_count"}:
        return formats.integer
    if metric_name == "new_revenue_share":
        return formats.percent
    if metric_name in {
        "total_revenue",
        "average_ticket",
        "new_revenue",
        "existing_revenue",
    }:
        return formats.currency
    return formats.text


def _write_summary_value(
    worksheet: Worksheet,
    row_index: int,
    metric_name: str,
    metric_value: object,
    formats: ReportFormats,
) -> None:
    """Write a typed summary cell with the right Excel format."""
    cell_format = _get_summary_format(metric_name, formats)
    if isinstance(metric_value, pd.Timestamp):
        worksheet.write_datetime(row_index, 1, metric_value.to_pydatetime(), cell_format)
        return
    if hasattr(metric_value, "year") and hasattr(metric_value, "month") and hasattr(metric_value, "day"):
        worksheet.write_datetime(row_index, 1, metric_value, cell_format)
        return
    if isinstance(metric_value, (int, float)) and metric_name not in {"period_start", "period_end"}:
        worksheet.write_number(row_index, 1, float(metric_value), cell_format)
        return
    worksheet.write(row_index, 1, metric_value, cell_format)


def _write_summary_sheet(
    writer: pd.ExcelWriter,
    overview_df: pd.DataFrame,
    formats: ReportFormats,
    generated_at: pd.Timestamp,
) -> None:
    """Create the business summary worksheet."""
    worksheet = writer.book.add_worksheet("Synthese")
    writer.sheets["Synthese"] = worksheet
    worksheet.hide_gridlines(2)
    worksheet.set_column("A:A", 34)
    worksheet.set_column("B:B", 22)

    worksheet.write("A1", "Rapport de ventes", formats.title)
    worksheet.write("A2", "Genere le", formats.metadata_label)
    worksheet.write_datetime("B2", generated_at.to_pydatetime(), formats.date)
    worksheet.write("A4", "Indicateur", formats.header)
    worksheet.write("B4", "Valeur", formats.header)
    worksheet.freeze_panes(4, 0)

    overview_map = {
        str(row["metric"]): row["value"]
        for _, row in overview_df.iterrows()
    }

    start_row = 4
    for offset, metric_name in enumerate(SUMMARY_ORDER, start=1):
        row_index = start_row + offset
        worksheet.write(row_index, 0, SUMMARY_LABELS[metric_name], formats.text)
        _write_summary_value(
            worksheet,
            row_index,
            metric_name,
            overview_map.get(metric_name, ""),
            formats,
        )


def _insert_monthly_trend_chart(
    workbook: Workbook,
    worksheet: Worksheet,
    monthly_df: pd.DataFrame,
) -> None:
    """Insert the revenue trend chart on the monthly worksheet."""
    required_columns = {"year_month", "revenue_total"}
    if monthly_df.empty or not required_columns.issubset(monthly_df.columns):
        return

    category_column = monthly_df.columns.get_loc("year_month")
    revenue_column = monthly_df.columns.get_loc("revenue_total")
    last_row = len(monthly_df)

    chart = workbook.add_chart({"type": "line"})
    chart.add_series(
        {
            "name": "CA total",
            "categories": ["Tendance_Mensuelle", 1, category_column, last_row, category_column],
            "values": ["Tendance_Mensuelle", 1, revenue_column, last_row, revenue_column],
            "line": {"color": "#2F5597", "width": 2.25},
            "marker": {"type": "circle", "size": 5, "border": {"color": "#2F5597"}},
        }
    )
    chart.set_title({"name": "Evolution mensuelle du chiffre d'affaires"})
    chart.set_x_axis({"name": "Mois"})
    chart.set_y_axis({"name": "Chiffre d'affaires", "major_gridlines": {"visible": False}})
    chart.set_legend({"position": "bottom"})
    worksheet.insert_chart("J2", chart, {"x_scale": 1.25, "y_scale": 1.15})


def create_management_report(
    output_dir: Path,
    kpis: KPIBundle,
    generated_at: pd.Timestamp | None = None,
) -> Path:
    """Generate the final stakeholder Excel report and return its path."""
    report_generated_at = generated_at or pd.Timestamp.now()
    report_output_path = build_report_output_path(output_dir, report_generated_at)
    normalized_kpis = _normalize_report_bundle(kpis)

    with pd.ExcelWriter(
        report_output_path,
        engine="xlsxwriter",
        date_format="yyyy-mm-dd",
        datetime_format="yyyy-mm-dd hh:mm:ss",
    ) as writer:
        workbook = writer.book
        formats = _build_report_formats(workbook)

        _write_summary_sheet(
            writer=writer,
            overview_df=normalized_kpis.overview,
            formats=formats,
            generated_at=report_generated_at,
        )
        monthly_sheet = _write_dataframe_sheet(
            writer=writer,
            sheet_name="Tendance_Mensuelle",
            dataframe=normalized_kpis.monthly,
            formats=formats,
        )
        _write_dataframe_sheet(
            writer=writer,
            sheet_name="Performance_Magasins",
            dataframe=normalized_kpis.by_store,
            formats=formats,
        )
        _write_dataframe_sheet(
            writer=writer,
            sheet_name="Performance_Offres",
            dataframe=normalized_kpis.by_plan,
            formats=formats,
        )
        _insert_monthly_trend_chart(
            workbook=workbook,
            worksheet=monthly_sheet,
            monthly_df=normalized_kpis.monthly,
        )

    return report_output_path
