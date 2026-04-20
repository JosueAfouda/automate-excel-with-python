"""Streamlit dashboard for sales analytics KPIs."""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytic.kpis import build_kpi_bundle
from src.runtime import get_outputs_root, get_runtime_root


def get_project_root() -> Path:
    """Return the root folder of the project."""
    return get_runtime_root()


def get_analytics_paths() -> dict[str, Path]:
    """Return the analytics CSV paths used by the dashboard."""
    analytics_dir = get_outputs_root() / "analytics"
    return {
        "overview": analytics_dir / "kpi_overview.csv",
        "monthly": analytics_dir / "monthly_kpis.csv",
        "by_store": analytics_dir / "kpis_by_store.csv",
        "by_plan": analytics_dir / "kpis_by_plan.csv",
        "quality": analytics_dir / "analytics_quality.csv",
        "file_inventory": analytics_dir / "analytics_file_inventory.csv",
    }


def get_reporting_paths() -> dict[str, Path]:
    """Return the CSV paths used by the reporting app."""
    paths = get_analytics_paths()
    paths["clean_sales_data"] = (
        get_outputs_root() / "transformation" / "clean_sales_data.csv"
    )
    return paths


def get_reporting_signatures(paths: dict[str, Path]) -> tuple[int, ...]:
    """Return file signatures used to invalidate Streamlit cache on data refresh."""
    return tuple(path.stat().st_mtime_ns for path in paths.values())


def get_latest_analytics_update() -> str:
    """Return the latest modification timestamp across analytics output files."""
    analytics_paths = get_analytics_paths()
    existing_paths = [path for path in analytics_paths.values() if path.exists()]
    if not existing_paths:
        return "n/a"

    latest_timestamp = max(path.stat().st_mtime for path in existing_paths)
    return pd.Timestamp.fromtimestamp(latest_timestamp).strftime("%Y-%m-%d %H:%M:%S")


def format_currency(value: float) -> str:
    """Format a numeric value as business-friendly currency."""
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    """Format a numeric value as a percentage."""
    return f"{value:.2%}"


def format_integer(value: float | int) -> str:
    """Format a numeric value as an integer string."""
    return f"{int(value):,}"


def build_overview_map(overview_df: pd.DataFrame) -> dict[str, object]:
    """Convert the overview KPI table into a dictionary."""
    if overview_df.empty:
        return {}

    return {
        str(row["metric"]): row["value"]
        for _, row in overview_df.iterrows()
    }


def normalize_dashboard_data(
    clean_df: pd.DataFrame,
    quality_df: pd.DataFrame,
    file_inventory_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Normalize dashboard inputs loaded from CSV."""
    clean_data = clean_df.copy()
    if not clean_data.empty:
        clean_data["transaction_date"] = pd.to_datetime(
            clean_data["transaction_date"],
            errors="coerce",
            format="mixed",
        )
        clean_data["month_start"] = pd.to_datetime(
            clean_data["month_start"],
            errors="coerce",
            format="mixed",
        )
        clean_data["amount"] = pd.to_numeric(clean_data["amount"], errors="coerce").fillna(0.0)
        for column in ["transaction_id", "store", "plan", "contract_type", "source_file", "source_folder", "year_month"]:
            clean_data[column] = clean_data[column].astype("string").fillna("").str.strip()
        clean_data = clean_data.sort_values(["transaction_date", "transaction_id"]).reset_index(drop=True)

    return clean_data, quality_df, file_inventory_df


@st.cache_data(show_spinner=False)
def load_dashboard_data(
    file_signatures: tuple[int, ...],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all datasets required by the dashboard."""
    del file_signatures
    paths = get_reporting_paths()
    missing_files = [str(path) for path in paths.values() if not path.exists()]
    if missing_files:
        raise FileNotFoundError(
            "Missing reporting inputs: " + ", ".join(missing_files)
        )

    clean_df = pd.read_csv(paths["clean_sales_data"])
    quality_df = pd.read_csv(paths["quality"])
    file_inventory_df = pd.read_csv(paths["file_inventory"])
    return normalize_dashboard_data(
        clean_df,
        quality_df,
        file_inventory_df,
    )


def apply_filters(
    clean_df: pd.DataFrame,
    selected_months: list[str],
    selected_stores: list[str],
    selected_plans: list[str],
) -> pd.DataFrame:
    """Apply dashboard filters to the cleaned sales data."""
    filtered = clean_df.copy()
    if selected_months:
        filtered = filtered[filtered["year_month"].isin(selected_months)]
    if selected_stores:
        filtered = filtered[filtered["store"].isin(selected_stores)]
    if selected_plans:
        filtered = filtered[filtered["plan"].isin(selected_plans)]
    return filtered.reset_index(drop=True)


def render_filter_summary(filtered_df: pd.DataFrame) -> None:
    """Render a short summary of the selected scope."""
    st.markdown("**Perimetre selectionne**")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    summary_col1.metric("Lignes nettoyees", format_integer(len(filtered_df)))
    summary_col2.metric("Fichiers source", format_integer(filtered_df["source_file"].nunique()))
    summary_col3.metric("Mois selectionnes", format_integer(filtered_df["year_month"].nunique()))


def render_overview_metrics(
    overview_map: dict[str, object],
    monthly_df: pd.DataFrame,
    file_inventory_df: pd.DataFrame,
) -> None:
    """Render the high-level business metrics."""
    total_revenue = float(overview_map.get("total_revenue", 0.0))
    total_transactions = float(overview_map.get("total_transactions", 0.0))
    average_ticket = float(overview_map.get("average_ticket", 0.0))
    stores_count = float(overview_map.get("stores_count", 0.0))
    new_revenue_share = float(overview_map.get("new_revenue_share", 0.0))
    months_covered = int(monthly_df["year_month"].nunique()) if not monthly_df.empty else 0
    files_processed = int(file_inventory_df["source_file"].nunique()) if not file_inventory_df.empty else 0

    latest_month_revenue = 0.0
    latest_growth = 0.0
    if not monthly_df.empty:
        latest_month_revenue = float(monthly_df.iloc[-1]["revenue_total"])
        latest_growth = float(monthly_df.iloc[-1]["growth_mom"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chiffre d'affaires total", format_currency(total_revenue))
    col2.metric("Transactions", format_integer(total_transactions))
    col3.metric("Panier moyen", format_currency(average_ticket))
    col4.metric("Magasins actifs", format_integer(stores_count))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Part nouveaux contrats", format_percent(new_revenue_share))
    col6.metric("Mois couverts", format_integer(months_covered))
    col7.metric("Fichiers analyses", format_integer(files_processed))
    col8.metric(
        "CA dernier mois",
        format_currency(latest_month_revenue),
        delta=format_percent(latest_growth),
    )


def render_monthly_section(monthly_df: pd.DataFrame) -> None:
    """Render the monthly KPI trends."""
    st.subheader("Performance mensuelle")

    if monthly_df.empty:
        st.info("Aucune donnee mensuelle disponible.")
        return

    revenue_chart = monthly_df.set_index("year_month")[
        ["revenue_total", "revenue_existing", "revenue_new"]
    ]
    st.line_chart(revenue_chart)

    growth_chart = monthly_df.set_index("year_month")[["growth_mom"]]
    st.bar_chart(growth_chart)

    monthly_display = monthly_df.copy()
    monthly_display["revenue_existing"] = monthly_display["revenue_existing"].map(format_currency)
    monthly_display["revenue_new"] = monthly_display["revenue_new"].map(format_currency)
    monthly_display["revenue_total"] = monthly_display["revenue_total"].map(format_currency)
    monthly_display["average_ticket"] = monthly_display["average_ticket"].map(format_currency)
    monthly_display["growth_mom"] = monthly_display["growth_mom"].map(format_percent)
    monthly_display["transactions"] = monthly_display["transactions"].map(format_integer)
    monthly_display["month_start"] = monthly_display["month_start"].dt.date.astype(str)
    st.dataframe(monthly_display, use_container_width=True, hide_index=True)


def render_dimension_section(
    title: str,
    dataframe: pd.DataFrame,
    dimension_column: str,
    top_n: int,
) -> None:
    """Render a ranked dimension table and chart."""
    st.subheader(title)

    if dataframe.empty:
        st.info("Aucune donnee disponible.")
        return

    top_df = dataframe.head(top_n).copy()
    chart_data = top_df.set_index(dimension_column)[["revenue"]]
    st.bar_chart(chart_data)

    display_df = top_df.copy()
    display_df["revenue"] = display_df["revenue"].map(format_currency)
    display_df["transactions"] = display_df["transactions"].map(format_integer)
    display_df["average_ticket"] = display_df["average_ticket"].map(format_currency)
    display_df["revenue_share"] = display_df["revenue_share"].map(format_percent)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_data_quality_section(
    quality_df: pd.DataFrame,
    file_inventory_df: pd.DataFrame,
) -> None:
    """Render the audit and data quality tables."""
    st.subheader("Suivi et qualite")

    quality_col, inventory_col = st.columns(2)

    with quality_col:
        st.markdown("**Qualite analytics**")
        if quality_df.empty:
            st.info("Aucun rapport de qualite disponible.")
        else:
            st.dataframe(quality_df.tail(10), use_container_width=True, hide_index=True)

    with inventory_col:
        st.markdown("**Inventaire des fichiers analyses**")
        if file_inventory_df.empty:
            st.info("Aucun inventaire disponible.")
        else:
            st.dataframe(file_inventory_df, use_container_width=True, hide_index=True)


def render_pipeline_audit_section(
    pipeline_quality_df: pd.DataFrame,
    pipeline_inventory_df: pd.DataFrame,
) -> None:
    """Render the full pipeline audit tables."""
    with st.expander("Audit complet du pipeline", expanded=False):
        st.markdown(
            "Ces tableaux refletent l'etat complet de l'etape analytics dans le pipeline, "
            "independamment des filtres du tableau de bord."
        )
        audit_col1, audit_col2 = st.columns(2)
        with audit_col1:
            st.markdown("**Historique des runs analytics**")
            st.dataframe(pipeline_quality_df.tail(10), use_container_width=True, hide_index=True)
        with audit_col2:
            st.markdown("**Inventaire analytics complet**")
            st.dataframe(pipeline_inventory_df, use_container_width=True, hide_index=True)


def main() -> None:
    """Render the Streamlit KPI dashboard."""
    st.set_page_config(
        page_title="Sales KPI Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Tableau de bord KPI des ventes")
    st.caption(
        "Ce tableau de bord lit directement les sorties analytics generees par le pipeline."
    )

    with st.sidebar:
        st.header("Parametres")
        top_n = st.slider("Top N pour les classements", min_value=3, max_value=10, value=6)
        if st.button("Rafraichir les donnees", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    reporting_paths = get_reporting_paths()

    try:
        file_signatures = get_reporting_signatures(reporting_paths)
        clean_df, pipeline_quality_df, pipeline_inventory_df = load_dashboard_data(
            file_signatures
        )
    except FileNotFoundError as error:
        st.error(str(error))
        st.info(
            "Execute d'abord le pipeline pour generer les fichiers de transformation et analytics, puis relance l'application Streamlit."
        )
        return

    available_months = sorted(clean_df["year_month"].dropna().unique().tolist())
    available_stores = sorted(clean_df["store"].dropna().unique().tolist())
    available_plans = sorted(clean_df["plan"].dropna().unique().tolist())

    with st.sidebar:
        selected_months = st.multiselect(
            "Mois",
            options=available_months,
            default=available_months,
        )
        selected_stores = st.multiselect(
            "Magasins",
            options=available_stores,
            default=available_stores,
        )
        selected_plans = st.multiselect(
            "Plans",
            options=available_plans,
            default=available_plans,
        )
        st.markdown("**Sources des donnees**")
        st.code(str(get_project_root() / "outputs" / "transformation"), language="text")
        st.code(str(get_project_root() / "outputs" / "analytics"), language="text")

    filtered_df = apply_filters(
        clean_df,
        selected_months,
        selected_stores,
        selected_plans,
    )

    if filtered_df.empty:
        st.warning("Aucune donnee ne correspond aux filtres selectionnes.")
        return

    filtered_bundle = build_kpi_bundle(filtered_df)
    overview_df = filtered_bundle.overview
    monthly_df = filtered_bundle.monthly
    by_store_df = filtered_bundle.by_store
    by_plan_df = filtered_bundle.by_plan
    quality_df = filtered_bundle.quality
    file_inventory_df = filtered_bundle.file_inventory

    overview_map = build_overview_map(overview_df)
    period_start = overview_map.get("period_start", "n/a")
    period_end = overview_map.get("period_end", "n/a")
    latest_update = get_latest_analytics_update()
    st.markdown(f"**Periode couverte :** {period_start} a {period_end}")
    st.caption(f"Derniere mise a jour : {latest_update}")
    render_filter_summary(filtered_df)

    render_overview_metrics(overview_map, monthly_df, file_inventory_df)
    st.divider()

    render_monthly_section(monthly_df)
    st.divider()

    store_col, plan_col = st.columns(2)
    with store_col:
        render_dimension_section("Performance par magasin", by_store_df, "store", top_n)
    with plan_col:
        render_dimension_section("Performance par plan", by_plan_df, "plan", top_n)

    st.divider()
    render_data_quality_section(quality_df, file_inventory_df)
    render_pipeline_audit_section(pipeline_quality_df, pipeline_inventory_df)


if __name__ == "__main__":
    main()
