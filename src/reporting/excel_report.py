"""Generate the final management report in Excel."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import pandas as pd
from xlsxwriter.format import Format
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from ..analytic.kpis import KPIBundle, normalize_dimension_kpis, normalize_monthly_kpis

LATEST_REPORT_FILENAME = "rapport_ventes_latest.xlsx"
REPORT_STATE_FILENAME = ".rapport_ventes_state.json"

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
    positive_text: Format
    negative_text: Format
    neutral_text: Format


@dataclass(frozen=True)
class ReportGenerationResult:
    """Result of the management report generation stage."""

    path: Path
    generated: bool
    fingerprint: str
    latest_month: str


def get_latest_report_path(output_dir: Path) -> Path:
    """Return the canonical path used for the current stakeholder workbook."""
    return output_dir / LATEST_REPORT_FILENAME


def get_report_state_path(output_dir: Path) -> Path:
    """Return the hidden state file used to detect unchanged report reruns."""
    return output_dir / REPORT_STATE_FILENAME


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
        positive_text=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "bold": True, "font_color": "#2E7D32"}
        ),
        negative_text=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "bold": True, "font_color": "#C62828"}
        ),
        neutral_text=workbook.add_format(
            {"font_name": "Calibri", "font_size": 11, "bold": True, "font_color": "#616161"}
        ),
    )


def _parse_overview_value(metric_name: str, raw_value: object) -> object:
    """Convert overview values to their reporting-friendly Python types."""
    if metric_name in {"period_start", "period_end"}:
        timestamp = pd.to_datetime(raw_value, errors="coerce")
        return timestamp.to_pydatetime() if pd.notna(timestamp) else str(raw_value)

    if metric_name in SUMMARY_ORDER:
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


def _get_latest_month_label(monthly_df: pd.DataFrame) -> str:
    """Return the latest covered business month."""
    if monthly_df.empty or "year_month" not in monthly_df.columns:
        return ""
    return str(monthly_df.iloc[-1]["year_month"])


def _get_comparison_month_labels(monthly_df: pd.DataFrame) -> tuple[str, str] | None:
    """Return the latest and previous month labels when available."""
    if len(monthly_df) < 2:
        return None
    previous_month = str(monthly_df.iloc[-2]["year_month"])
    latest_month = str(monthly_df.iloc[-1]["year_month"])
    return previous_month, latest_month


def _write_summary_sheet(
    writer: pd.ExcelWriter,
    overview_df: pd.DataFrame,
    monthly_df: pd.DataFrame,
    formats: ReportFormats,
    generated_at: pd.Timestamp,
) -> None:
    """Create the business summary worksheet."""
    worksheet = writer.book.add_worksheet("Synthese")
    writer.sheets["Synthese"] = worksheet
    worksheet.hide_gridlines(2)
    worksheet.set_column("A:A", 34)
    worksheet.set_column("B:B", 22)

    latest_month = _get_latest_month_label(monthly_df) or "n/a"
    comparison_labels = _get_comparison_month_labels(monthly_df)
    comparison_label = (
        f"{comparison_labels[1]} vs {comparison_labels[0]}"
        if comparison_labels
        else "Comparaison indisponible"
    )

    worksheet.write("A1", "Rapport de ventes", formats.title)
    worksheet.write("A2", "Genere le", formats.metadata_label)
    worksheet.write_datetime("B2", generated_at.to_pydatetime(), formats.date)
    worksheet.write("A3", "Dernier mois couvert", formats.metadata_label)
    worksheet.write("B3", latest_month, formats.metadata_value)
    worksheet.write("A4", "Comparaison", formats.metadata_label)
    worksheet.write("B4", comparison_label, formats.metadata_value)
    worksheet.write("A6", "Indicateur", formats.header)
    worksheet.write("B6", "Valeur", formats.header)
    worksheet.freeze_panes(6, 0)

    overview_map = {
        str(row["metric"]): row["value"]
        for _, row in overview_df.iterrows()
    }

    start_row = 6
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


def _get_trend_label(delta: float) -> str:
    """Return a business-friendly label for a delta."""
    if delta > 0:
        return "Hausse"
    if delta < 0:
        return "Baisse"
    return "Stable"


def _get_trend_format(delta: float, formats: ReportFormats) -> Format:
    """Return the text format used to highlight change direction."""
    if delta > 0:
        return formats.positive_text
    if delta < 0:
        return formats.negative_text
    return formats.neutral_text


def _safe_relative_variation(current_value: float, previous_value: float) -> float | None:
    """Return the relative variation when it is mathematically valid."""
    if previous_value == 0:
        return None
    return (current_value / previous_value) - 1


def _write_number_or_blank(
    worksheet: Worksheet,
    row_index: int,
    column_index: int,
    value: float | int | None,
    cell_format: Format,
) -> None:
    """Write a number when available, or leave the cell blank."""
    if value is None or pd.isna(value):
        worksheet.write_blank(row_index, column_index, None, cell_format)
        return
    worksheet.write_number(row_index, column_index, float(value), cell_format)


def _write_monthly_comparison_sheet(
    writer: pd.ExcelWriter,
    monthly_df: pd.DataFrame,
    formats: ReportFormats,
) -> None:
    """Create a sheet comparing the latest month to the previous one."""
    worksheet = writer.book.add_worksheet("Comparaison_Mensuelle")
    writer.sheets["Comparaison_Mensuelle"] = worksheet
    worksheet.hide_gridlines(2)
    worksheet.set_column("A:A", 32)
    worksheet.set_column("B:E", 18)
    worksheet.set_column("F:F", 14)

    worksheet.write("A1", "Comparaison mensuelle", formats.title)

    if len(monthly_df) < 2:
        worksheet.write(
            "A3",
            "Au moins deux mois sont necessaires pour calculer une comparaison.",
            formats.text,
        )
        return

    previous_row = monthly_df.iloc[-2]
    current_row = monthly_df.iloc[-1]
    previous_month = str(previous_row["year_month"])
    current_month = str(current_row["year_month"])

    comparison_rows = [
        {
            "label": "Chiffre d'affaires total",
            "kind": "currency",
            "previous": float(previous_row["revenue_total"]),
            "current": float(current_row["revenue_total"]),
        },
        {
            "label": "CA contrats existants",
            "kind": "currency",
            "previous": float(previous_row["revenue_existing"]),
            "current": float(current_row["revenue_existing"]),
        },
        {
            "label": "CA nouveaux contrats",
            "kind": "currency",
            "previous": float(previous_row["revenue_new"]),
            "current": float(current_row["revenue_new"]),
        },
        {
            "label": "Transactions",
            "kind": "integer",
            "previous": float(previous_row["transactions"]),
            "current": float(current_row["transactions"]),
        },
        {
            "label": "Panier moyen",
            "kind": "currency",
            "previous": float(previous_row["average_ticket"]),
            "current": float(current_row["average_ticket"]),
        },
        {
            "label": "Part nouveaux contrats",
            "kind": "percent",
            "previous": (
                float(previous_row["revenue_new"]) / float(previous_row["revenue_total"])
                if float(previous_row["revenue_total"]) else 0.0
            ),
            "current": (
                float(current_row["revenue_new"]) / float(current_row["revenue_total"])
                if float(current_row["revenue_total"]) else 0.0
            ),
        },
        {
            "label": "Croissance mensuelle",
            "kind": "percent",
            "previous": float(previous_row["growth_mom"]),
            "current": float(current_row["growth_mom"]),
        },
    ]

    worksheet.write("A2", "Periode comparee", formats.metadata_label)
    worksheet.write("B2", f"{current_month} vs {previous_month}", formats.metadata_value)

    headers = [
        "Indicateur",
        previous_month,
        current_month,
        "Delta",
        "Variation %",
        "Tendance",
    ]
    header_row = 3
    for column_index, header in enumerate(headers):
        worksheet.write(header_row, column_index, header, formats.header)

    worksheet.freeze_panes(header_row + 1, 0)

    for offset, row in enumerate(comparison_rows, start=1):
        row_index = header_row + offset
        previous_value = row["previous"]
        current_value = row["current"]
        delta_value = current_value - previous_value
        variation_pct = (
            None
            if row["kind"] == "percent"
            else _safe_relative_variation(current_value, previous_value)
        )

        if row["kind"] == "currency":
            number_format = formats.currency
        elif row["kind"] == "integer":
            number_format = formats.integer
        else:
            number_format = formats.percent

        worksheet.write(row_index, 0, row["label"], formats.text)
        _write_number_or_blank(worksheet, row_index, 1, previous_value, number_format)
        _write_number_or_blank(worksheet, row_index, 2, current_value, number_format)
        _write_number_or_blank(worksheet, row_index, 3, delta_value, number_format)
        _write_number_or_blank(worksheet, row_index, 4, variation_pct, formats.percent)
        worksheet.write(
            row_index,
            5,
            _get_trend_label(delta_value),
            _get_trend_format(delta_value, formats),
        )


def _json_safe_records(dataframe: pd.DataFrame) -> list[dict[str, object]]:
    """Convert a dataframe into stable JSON-serializable records."""
    if dataframe.empty:
        return []

    serializable = dataframe.copy()
    for column_name in serializable.columns:
        column = serializable[column_name]
        if pd.api.types.is_datetime64_any_dtype(column):
            serializable[column_name] = column.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
        else:
            serializable[column_name] = column.where(column.notna(), "").astype(str)

    return serializable.to_dict(orient="records")


def build_report_fingerprint(kpis: KPIBundle) -> str:
    """Build a stable fingerprint from the business-facing report inputs."""
    payload = {
        "overview": _json_safe_records(kpis.overview),
        "monthly": _json_safe_records(kpis.monthly),
        "by_store": _json_safe_records(kpis.by_store),
        "by_plan": _json_safe_records(kpis.by_plan),
    }
    serialized_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def _read_report_state(state_path: Path) -> dict[str, str]:
    """Read the previous report state if available."""
    if not state_path.exists():
        return {}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_report_state(
    state_path: Path,
    fingerprint: str,
    latest_month: str,
    generated_at: pd.Timestamp,
) -> None:
    """Persist the metadata used to detect unchanged reruns."""
    state_payload = {
        "fingerprint": fingerprint,
        "latest_month": latest_month,
        "generated_at": generated_at.isoformat(),
    }
    state_path.write_text(
        json.dumps(state_payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def _cleanup_old_reports(output_dir: Path, latest_report_path: Path) -> None:
    """Remove outdated report files so only the current workbook remains visible."""
    for candidate_path in output_dir.glob("rapport_ventes*.xlsx"):
        if candidate_path == latest_report_path:
            continue
        candidate_path.unlink(missing_ok=True)


def create_management_report(
    output_dir: Path,
    kpis: KPIBundle,
    generated_at: pd.Timestamp | None = None,
) -> ReportGenerationResult:
    """Generate or reuse the current stakeholder Excel report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_generated_at = generated_at or pd.Timestamp.now()
    normalized_kpis = _normalize_report_bundle(kpis)
    report_path = get_latest_report_path(output_dir)
    state_path = get_report_state_path(output_dir)
    latest_month = _get_latest_month_label(normalized_kpis.monthly)
    fingerprint = build_report_fingerprint(normalized_kpis)
    previous_state = _read_report_state(state_path)

    if previous_state.get("fingerprint") == fingerprint and report_path.exists():
        _cleanup_old_reports(output_dir, report_path)
        return ReportGenerationResult(
            path=report_path,
            generated=False,
            fingerprint=fingerprint,
            latest_month=latest_month,
        )

    temporary_report_path = output_dir / ".rapport_ventes_latest.tmp.xlsx"
    if temporary_report_path.exists():
        temporary_report_path.unlink()

    with pd.ExcelWriter(
        temporary_report_path,
        engine="xlsxwriter",
        date_format="yyyy-mm-dd",
        datetime_format="yyyy-mm-dd hh:mm:ss",
    ) as writer:
        workbook = writer.book
        formats = _build_report_formats(workbook)

        _write_summary_sheet(
            writer=writer,
            overview_df=normalized_kpis.overview,
            monthly_df=normalized_kpis.monthly,
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
        _write_monthly_comparison_sheet(
            writer=writer,
            monthly_df=normalized_kpis.monthly,
            formats=formats,
        )
        _insert_monthly_trend_chart(
            workbook=workbook,
            worksheet=monthly_sheet,
            monthly_df=normalized_kpis.monthly,
        )

    temporary_report_path.replace(report_path)
    _write_report_state(state_path, fingerprint, latest_month, report_generated_at)
    _cleanup_old_reports(output_dir, report_path)

    return ReportGenerationResult(
        path=report_path,
        generated=True,
        fingerprint=fingerprint,
        latest_month=latest_month,
    )
