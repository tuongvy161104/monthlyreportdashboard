from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


st.set_page_config(
    page_title="Gems United | Mar 2026 Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


DATA_PATH = Path(__file__).with_name("AllAccountReport-Mar2026.csv")
LOGO_PATH = Path(__file__).with_name("main.png")

ACCOUNT_COL = "Account name"
CAMPAIGN_COL = "Campaign name"
COUNTRY_COL = "Country"
DAY_COL = "Day"
SPEND_COL = "Amount spent (USD)"
SALES_COL = "Purchases conversion value"
PURCHASES_COL = "Purchases"
CPP_COL = "Cost per purchase"
CTR_COL = "CTR (link click-through rate)"
CPC_COL = "CPC (cost per link click)"
CPM_COL = "CPM (cost per 1,000 impressions)"
MEDIA_TYPE_COL = "Parsed Media Type"
PRODUCT_ID_COL = "Parsed Product ID"
PRODUCT_COL = "Parsed Product"
NICHE_COL = "Parsed Niche"

REQUIRED_COLUMNS = {
    ACCOUNT_COL,
    COUNTRY_COL,
    DAY_COL,
    SPEND_COL,
    SALES_COL,
    PURCHASES_COL,
    CPP_COL,
}

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
COUNTRY_ORDER = ["US", "CA", "AU", "GB", "ES", "FR", "IT", "unknown"]
OVERVIEW_DEFAULT_COUNTRIES = ["US", "CA", "AU", "GB"]
SPEND_COLOR = "#C6715C"
PURCHASE_COLOR = "#B08D57"
ROAS_COLOR = "#5F8F5A"
SALES_COLOR = "#7D9C69"
CPP_COLOR = "#B45A46"
CTR_COLOR = "#8A6942"
THEME_PAPER_BG = "rgba(251,246,238,0.96)"
THEME_PLOT_BG = "rgba(255,252,247,0.95)"
THEME_TREEMAP_SCALE = [[0.0, "#F2E7D5"], [0.5, "#D6B58A"], [1.0, "#8E6840"]]
MEDIA_TYPE_COLORS = {
    "MOVIDAI": "#8FA68C",
    "IMG": "#C9B26A",
    "VID": "#B58B8B",
}
PRODUCT_STATUS_ORDER = ["Star", "Optimize", "Potentials", "Cut"]
PRODUCT_STATUS_COLORS = {
    "Star": "#DCEFD9",
    "Optimize": "#FBE8B3",
    "Potentials": "#DCEBFF",
    "Cut": "#F8DAD7",
}
PRODUCT_STATUS_MARKER_COLORS = {
    "Star": "#4D8F4B",
    "Optimize": "#C89B2C",
    "Potentials": "#4E7CBF",
    "Cut": "#C75B4D",
}
PRODUCT_STATUS_ICONS = {
    "Star": "⭐",
    "Optimize": "🔧",
    "Potentials": "🌱",
    "Cut": "❌",
}
ACCOUNT_ORDER = ["MX-B-04-51", "MX-B-04-52", "MX-B-04-53", "MX-W-04-100"]
ACCOUNT_CHART_KEY = "account_chart"
COUNTRY_PURCHASE_CHART_KEY = "country_purchase_chart"
WEEKDAY_CHART_KEY = "weekday_chart"
COUNTRY_SPEND_CHART_KEY = "country_spend_chart"
CONTENT_MEDIA_PURCHASE_CHART_KEY = "content_media_purchase_chart"
CONTENT_SPEND_ROAS_CHART_KEY = "content_spend_roas_chart"
CONTENT_CPC_CTR_CHART_KEY = "content_cpc_ctr_chart"
CONTENT_NICHE_TREEMAP_KEY = "content_niche_treemap"
CONTENT_PRODUCT_TREEMAP_KEY = "content_product_treemap"


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def parse_campaign_taxonomy(campaign_series: pd.Series) -> pd.DataFrame:
    campaign_text = campaign_series.astype("string").fillna("")
    # Supports both naming styles where product_id is the first token in campaign name.
    product_id = campaign_text.str.extract(r"^\s*([A-Za-z]+\d+_[A-Za-z0-9]+)\b", expand=False)
    product_id = product_id.astype("string").str.upper().fillna("UNKNOWN_0")

    parts = product_id.str.extract(r"^([A-Za-z]+)(\d+)_([A-Za-z0-9]+)$")
    niche = parts[0].astype("string").str.upper().fillna("UNKNOWN")
    product = parts[2].astype("string").str.upper().fillna("UNKNOWN")

    return pd.DataFrame(
        {
            PRODUCT_ID_COL: product_id,
            NICHE_COL: niche,
            PRODUCT_COL: product,
        }
    )


def parse_media_type(campaign_series: pd.Series) -> pd.Series:
    campaign_text = campaign_series.astype("string").fillna("")
    matched = campaign_text.str.extract(r"(?i)\b(MOVIDAI|IMG|VID)\b", expand=False)
    return matched.astype("string").str.upper().fillna("IMG")


def normalize_media_type(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.upper().str.strip()
    return normalized.replace({"": "IMG", "UNKNOWN": "IMG", "NAN": "IMG"}).fillna("IMG")


def ensure_product_columns(df: pd.DataFrame) -> pd.DataFrame:
    if PRODUCT_ID_COL in df.columns and PRODUCT_COL in df.columns and NICHE_COL in df.columns:
        ensured = df.copy()
        if MEDIA_TYPE_COL in ensured.columns:
            ensured[MEDIA_TYPE_COL] = normalize_media_type(ensured[MEDIA_TYPE_COL])
        return ensured
    if CAMPAIGN_COL not in df.columns:
        return df

    ensured = df.copy()
    taxonomy = parse_campaign_taxonomy(ensured[CAMPAIGN_COL])
    ensured[PRODUCT_ID_COL] = taxonomy[PRODUCT_ID_COL]
    ensured[NICHE_COL] = taxonomy[NICHE_COL]
    ensured[PRODUCT_COL] = taxonomy[PRODUCT_COL]
    ensured[MEDIA_TYPE_COL] = parse_media_type(ensured[CAMPAIGN_COL])
    return ensured


@st.cache_data(show_spinner=True)
def load_data() -> pd.DataFrame:
    raise RuntimeError("Local data loading is disabled. Upload a file to view the dashboard.")


@st.cache_data(show_spinner=False)
def load_logo_data_uri(path_str: str) -> str | None:
    logo_path = Path(path_str)
    if not logo_path.exists():
        return None
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def normalize_data(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    missing_columns = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing_columns:
        st.error(
            f"File '{source_name}' is missing required columns: {', '.join(missing_columns)}"
        )
        st.stop()

    normalized = df.copy()
    normalized[DAY_COL] = pd.to_datetime(normalized[DAY_COL], errors="coerce")
    for column in [SPEND_COL, SALES_COL, PURCHASES_COL, CPP_COL]:
        normalized[column] = _to_numeric(normalized[column])
    for optional_column in [CTR_COL, CPC_COL, CPM_COL]:
        if optional_column in normalized.columns:
            normalized[optional_column] = _to_numeric(normalized[optional_column])
    normalized[ACCOUNT_COL] = normalized[ACCOUNT_COL].astype("string").fillna("Unknown")
    normalized[COUNTRY_COL] = normalized[COUNTRY_COL].astype("string").fillna("unknown")
    if CAMPAIGN_COL in normalized.columns:
        normalized[CAMPAIGN_COL] = normalized[CAMPAIGN_COL].astype("string").fillna("Unknown Campaign")
        taxonomy = parse_campaign_taxonomy(normalized[CAMPAIGN_COL])
        normalized[PRODUCT_ID_COL] = taxonomy[PRODUCT_ID_COL]
        normalized[NICHE_COL] = taxonomy[NICHE_COL]
        normalized[PRODUCT_COL] = taxonomy[PRODUCT_COL]
        normalized[MEDIA_TYPE_COL] = parse_media_type(normalized[CAMPAIGN_COL])
    elif MEDIA_TYPE_COL in normalized.columns:
        normalized[MEDIA_TYPE_COL] = normalize_media_type(normalized[MEDIA_TYPE_COL])
    normalized["Weekday"] = pd.Categorical(normalized[DAY_COL].dt.day_name(), categories=WEEKDAY_ORDER, ordered=True)
    normalized.attrs["source_name"] = source_name
    return normalized


@st.cache_data(show_spinner=True)
def load_uploaded_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    buffer = pd.io.common.BytesIO(file_bytes)
    suffix = Path(file_name).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        uploaded_df = pd.read_excel(buffer)
    else:
        uploaded_df = pd.read_csv(buffer)
    return normalize_data(uploaded_df, source_name=file_name)


def build_options(values: pd.Series, preferred_order: list[str] | None = None) -> list[str]:
    unique_values = [value for value in values.dropna().astype(str).unique().tolist() if value]
    if not preferred_order:
        return sorted(unique_values)

    ordered = [value for value in preferred_order if value in unique_values]
    leftovers = sorted(value for value in unique_values if value not in ordered)
    return ordered + leftovers


def selection_values_from_state(widget_state: object) -> list[str]:
    if widget_state is None:
        return []

    selection = getattr(widget_state, "selection", widget_state)
    if isinstance(selection, dict):
        points = selection.get("points", [])
    else:
        points = getattr(selection, "points", [])

    values: list[str] = []
    for point in points or []:
        candidate_values: list[object] = []
        if isinstance(point, dict):
            candidate_values.extend([
                point.get("x"),
                point.get("label"),
                point.get("id"),
                point.get("parent"),
            ])
            customdata = point.get("customdata")
            if isinstance(customdata, (list, tuple)):
                candidate_values.extend(customdata)
        else:
            candidate_values.extend([
                getattr(point, "x", None),
                getattr(point, "label", None),
                getattr(point, "id", None),
                getattr(point, "parent", None),
            ])
            customdata = getattr(point, "customdata", None)
            if isinstance(customdata, (list, tuple)):
                candidate_values.extend(customdata)

        for value in candidate_values:
            if value is not None and str(value):
                values.append(str(value))

    return list(dict.fromkeys(values))


def selected_values_from_chart_key(key: str) -> list[str]:
    return selection_values_from_state(st.session_state.get(key))


def clear_chart_selection_keys(keys: list[str]) -> None:
    for key in keys:
        st.session_state.pop(key, None)


def compact_chart(fig: go.Figure) -> go.Figure:
    # Remove extra UI tracks and keep each chart compact.
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5D492F"),
    )
    return fig


def media_type_bar_colors(values: pd.Series) -> list[str]:
    normalized = values.astype("string").str.upper()
    return [MEDIA_TYPE_COLORS.get(value, "#9aa0a6") for value in normalized]


def money_short(value: float) -> str:
    value = 0.0 if pd.isna(value) else float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.0f}K"
    return f"{sign}${value:.0f}"


def format_ratio(value: float) -> str:
    if pd.isna(value):
        return "0.00"
    return f"{value:.2f}"


def metric_card(title: str, value: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """


def chart_title(text: str) -> None:
    st.markdown(f'<div class="chart-title">{text}</div>', unsafe_allow_html=True)


def format_pct(value: float) -> str:
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1%}"


def get_report_month_year(df: pd.DataFrame) -> str:
    """Extract month and year from DAY column in English format (Month YYYY)."""
    if df.empty or DAY_COL not in df.columns:
        return "Unknown Period"
    
    valid_dates = pd.to_datetime(df[DAY_COL], errors="coerce").dropna()
    if valid_dates.empty:
        return "Unknown Period"
    
    # Get the latest date to determine the report period
    latest_date = valid_dates.max()
    month_name = latest_date.strftime("%B")
    year = latest_date.year
    return f"{month_name} {year}"


def status_display_label(status: str) -> str:
    icon = PRODUCT_STATUS_ICONS.get(status, "")
    return f"{icon} {status}".strip()


def classify_product_performance(summary: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    classified = summary.copy()

    positive_purchases = classified[classified[PURCHASES_COL] > 0][PURCHASES_COL]
    positive_roas = classified[classified["ROAS"].fillna(0) > 0]["ROAS"]

    purchase_threshold = float(positive_purchases.median()) if not positive_purchases.empty else float(classified[PURCHASES_COL].median())
    roas_threshold = float(positive_roas.median()) if not positive_roas.empty else float(classified["ROAS"].median())

    def _status(row: pd.Series) -> str:
        purchases_value = row[PURCHASES_COL]
        roas_value = row["ROAS"]
        purchases = 0.0 if pd.isna(purchases_value) else float(purchases_value)
        roas = 0.0 if pd.isna(roas_value) else float(roas_value)
        if purchases >= purchase_threshold and roas >= roas_threshold:
            return "Star"
        if purchases >= purchase_threshold and roas < roas_threshold:
            return "Optimize"
        if purchases < purchase_threshold and roas >= roas_threshold:
            return "Potentials"
        return "Cut"

    classified["Status"] = classified.apply(_status, axis=1)
    classified["Status Rank"] = classified["Status"].map({name: index for index, name in enumerate(PRODUCT_STATUS_ORDER)})
    classified = classified.sort_values([PURCHASES_COL, "ROAS"], ascending=[False, False])
    return classified, purchase_threshold, roas_threshold


def build_product_scatter_chart(summary: pd.DataFrame, purchase_threshold: float, roas_threshold: float, product_metric: str = PRODUCT_COL) -> go.Figure:
    fig = go.Figure()

    for status in PRODUCT_STATUS_ORDER:
        subset = summary[summary["Status"] == status]
        if subset.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=subset[PURCHASES_COL],
                y=subset["ROAS"],
                mode="markers",
                name=status,
                marker=dict(
                    size=12,
                    color=PRODUCT_STATUS_MARKER_COLORS[status],
                    line=dict(color="#ffffff", width=0.9),
                    opacity=0.9,
                ),
                customdata=subset[[product_metric, SPEND_COL, SALES_COL, PURCHASES_COL, "ROAS", "Status"]].to_numpy(),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Purchases: %{customdata[3]:,.0f}<br>"
                    "ROAS: %{customdata[4]:.2f}<br>"
                    "Revenue: $%{customdata[2]:,.0f}<br>"
                    "Amount spent: $%{customdata[1]:,.0f}<br>"
                    "Status: %{customdata[5]}<extra></extra>"
                ),
            )
        )

    fig.add_vline(x=purchase_threshold, line_width=1.5, line_dash="dash", line_color="#9C7A4A")
    fig.add_hline(y=roas_threshold, line_width=1.5, line_dash="dash", line_color="#9C7A4A")
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=520,
        template="plotly_white",
        title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(title_text="Purchases", showgrid=True)
    fig.update_yaxes(title_text="ROAS", showgrid=True)
    return compact_chart(fig)


def render_product_status_grid(scale_count: int, optimize_count: int, test_count: int, cut_count: int) -> None:
    """Render a 2x2 grid matrix showing product status distribution."""
    container_html = (
        '<div style="background-color: #ffffff; border: 1px solid rgba(146, 115, 76, 0.22); border-radius: 12px; padding: 1.25rem; margin: 0.25rem 0 1rem 0;">'
        '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">'
        '<div style="background-color: #DCEFD9; border: 2px solid #4f3b24; padding: 1.6rem 1.2rem; text-align: center; border-radius: 8px;">'
        f'<div style="font-weight: 800; font-size: 2.1rem; color: #4f3b24; margin-bottom: 0.45rem;">{scale_count}</div>'
        '<div style="font-weight: 700; font-size: 1rem; color: #4f3b24;">⭐ STAR</div>'
        '</div>'
        '<div style="background-color: #FBE8B3; border: 2px solid #4f3b24; padding: 1.6rem 1.2rem; text-align: center; border-radius: 8px;">'
        f'<div style="font-weight: 800; font-size: 2.1rem; color: #4f3b24; margin-bottom: 0.45rem;">{optimize_count}</div>'
        '<div style="font-weight: 700; font-size: 1rem; color: #4f3b24;">🔧 OPTIMIZE</div>'
        '</div>'
        '<div style="background-color: #DCEBFF; border: 2px solid #4f3b24; padding: 1.6rem 1.2rem; text-align: center; border-radius: 8px;">'
        f'<div style="font-weight: 800; font-size: 2.1rem; color: #4f3b24; margin-bottom: 0.45rem;">{test_count}</div>'
        '<div style="font-weight: 700; font-size: 1rem; color: #4f3b24;">🌱 POTENTIALS</div>'
        '</div>'
        '<div style="background-color: #F8DAD7; border: 2px solid #4f3b24; padding: 1.6rem 1.2rem; text-align: center; border-radius: 8px;">'
        f'<div style="font-weight: 800; font-size: 2.1rem; color: #4f3b24; margin-bottom: 0.45rem;">{cut_count}</div>'
        '<div style="font-weight: 700; font-size: 1rem; color: #4f3b24;">❌ CUT</div>'
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(container_html, unsafe_allow_html=True)


def render_product_insights(summary: pd.DataFrame, purchase_threshold: float, roas_threshold: float) -> None:
    total_purchases = summary[PURCHASES_COL].sum(skipna=True)
    total_spend = summary[SPEND_COL].sum(skipna=True)

    top3_share = summary.head(3)[PURCHASES_COL].sum() / total_purchases if total_purchases else 0.0
    cut_spend_share = summary.loc[summary["Status"] == "Cut", SPEND_COL].sum() / total_spend if total_spend else 0.0
    low_volume_high_roas = summary[(summary["Status"] == "Potentials") & (summary["ROAS"] >= roas_threshold)]
    star_count = int((summary["Status"] == "Star").sum())
    optimize_count = int((summary["Status"] == "Optimize").sum())
    potentials_count = int((summary["Status"] == "Potentials").sum())
    cut_count = int((summary["Status"] == "Cut").sum())

    st.markdown(
        f"""
        <div class="insight-panel">
            <div class="insight-title">Key Product Insights</div>
            <ul class="insight-list">
                <li>Status mix: {star_count} Star, {optimize_count} Optimize, {potentials_count} Potentials, {cut_count} Cut.</li>
                <li>Top 3 products contribute {format_pct(top3_share)} of total purchases.</li>
                <li>Cut products consume {format_pct(cut_spend_share)} of spend.</li>
                <li>{len(low_volume_high_roas)} low-volume products are in Potentials status with ROAS above the median threshold.</li>
                <li>Thresholds used: Purchases at {purchase_threshold:,.0f} and ROAS at {roas_threshold:.2f}.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_filters(
    df: pd.DataFrame,
    accounts: list[str],
    countries: list[str],
    weekdays: list[str],
    media_types: list[str] | None = None,
) -> pd.DataFrame:
    filtered = df.copy()
    if accounts:
        filtered = filtered[filtered[ACCOUNT_COL].isin(accounts)]
    if countries:
        filtered = filtered[filtered[COUNTRY_COL].isin(countries)]
    if weekdays:
        filtered = filtered[filtered["Weekday"].astype(str).isin(weekdays)]
    if media_types and MEDIA_TYPE_COL in filtered.columns:
        filtered = filtered[filtered[MEDIA_TYPE_COL].isin(media_types)]
    return filtered


def build_account_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(ACCOUNT_COL, as_index=False)[[SPEND_COL, SALES_COL]]
        .sum(numeric_only=True)
        .sort_values(SPEND_COL, ascending=False)
    )
    fig = go.Figure()
    fig.add_bar(name="Amount spent", x=grouped[ACCOUNT_COL], y=grouped[SPEND_COL], marker_color=SPEND_COLOR)
    fig.add_bar(name="Revenue", x=grouped[ACCOUNT_COL], y=grouped[SALES_COL], marker_color=SALES_COLOR)
    fig.update_layout(
        barmode="stack",
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        title_text="",
    )
    fig.update_yaxes(tickprefix="$")
    return compact_chart(fig)


def build_country_purchase_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(COUNTRY_COL, as_index=False)[[SPEND_COL, PURCHASES_COL]]
        .sum(numeric_only=True)
        .assign(**{CPP_COL: lambda frame: frame[SPEND_COL].div(frame[PURCHASES_COL].replace(0, pd.NA))})
        .reindex(columns=[COUNTRY_COL, PURCHASES_COL, CPP_COL])
    )
    grouped[COUNTRY_COL] = pd.Categorical(grouped[COUNTRY_COL], categories=COUNTRY_ORDER, ordered=True)
    grouped = grouped.sort_values(COUNTRY_COL)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(name="Purchases", x=grouped[COUNTRY_COL].astype(str), y=grouped[PURCHASES_COL], marker_color=PURCHASE_COLOR, secondary_y=False)
    fig.add_scatter(name="Cost per purchase", x=grouped[COUNTRY_COL].astype(str), y=grouped[CPP_COL], mode="lines+markers", line=dict(color=CPP_COLOR, width=3), secondary_y=True)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        template="plotly_white",
        title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Purchases", secondary_y=False)
    fig.update_yaxes(title_text="Cost per purchase", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_weekday_roas_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby("Weekday", observed=False, as_index=False)
        .agg({PURCHASES_COL: "sum", SPEND_COL: "sum", SALES_COL: "sum"})
        .assign(ROAS=lambda frame: frame[SALES_COL].div(frame[SPEND_COL].replace(0, pd.NA)))
    )
    grouped["Weekday"] = pd.Categorical(grouped["Weekday"], categories=WEEKDAY_ORDER, ordered=True)
    grouped = grouped.sort_values("Weekday")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        name="Purchases",
        x=grouped["Weekday"].astype(str),
        y=grouped[PURCHASES_COL],
        marker_color=["#8A6A42", "#96754A", "#A28053", "#AE8C5D", "#BB9768", "#C8A473", "#D6B283"],
    )
    fig.add_scatter(name="ROAS", x=grouped["Weekday"].astype(str), y=grouped["ROAS"], mode="lines+markers", line=dict(color=ROAS_COLOR, width=3), secondary_y=True)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        template="plotly_white",
        title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Purchases", secondary_y=False)
    fig.update_yaxes(title_text="ROAS", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_country_spend_roas_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(COUNTRY_COL, as_index=False)[[SPEND_COL, SALES_COL]]
        .sum(numeric_only=True)
        .assign(ROAS=lambda frame: frame[SALES_COL].div(frame[SPEND_COL].replace(0, pd.NA)))
    )
    grouped[COUNTRY_COL] = pd.Categorical(grouped[COUNTRY_COL], categories=COUNTRY_ORDER, ordered=True)
    grouped = grouped.sort_values(COUNTRY_COL)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(name="Amount spent", x=grouped[COUNTRY_COL].astype(str), y=grouped[SPEND_COL], marker_color=SPEND_COLOR, secondary_y=False)
    fig.add_scatter(name="ROAS", x=grouped[COUNTRY_COL].astype(str), y=grouped["ROAS"], mode="lines+markers", line=dict(color=ROAS_COLOR, width=3), secondary_y=True)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=360,
        template="plotly_white",
        title_text="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Amount spent (USD)", secondary_y=False)
    fig.update_yaxes(title_text="ROAS", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_product_metric_summary(df: pd.DataFrame, metric_col: str) -> pd.DataFrame:
    if metric_col not in df.columns:
        return pd.DataFrame(columns=[metric_col, PURCHASES_COL, "Average CPP", "ROAS"])

    agg_dict = {
        SPEND_COL: "sum",
        SALES_COL: "sum",
        PURCHASES_COL: "sum",
    }
    
    # Preserve PRODUCT_COL, PRODUCT_ID_COL and NICHE_COL if they exist
    if PRODUCT_COL in df.columns:
        agg_dict[PRODUCT_COL] = "first"
    if PRODUCT_ID_COL in df.columns:
        agg_dict[PRODUCT_ID_COL] = "first"
    if NICHE_COL in df.columns:
        agg_dict[NICHE_COL] = "first"

    grouped = (
        df.groupby(metric_col, as_index=False, dropna=False)
        .agg(agg_dict)
        .assign(
            **{
                "Average CPP": lambda frame: frame[SPEND_COL].div(frame[PURCHASES_COL].replace(0, pd.NA)),
                "ROAS": lambda frame: frame[SALES_COL].div(frame[SPEND_COL].replace(0, pd.NA)),
            }
        )
        .sort_values(PURCHASES_COL, ascending=False)
    )
    return grouped


def build_content_media_purchase_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(MEDIA_TYPE_COL, as_index=False)[[PURCHASES_COL, SPEND_COL, SALES_COL]]
        .sum(numeric_only=True)
        .assign(LaunchRate=lambda frame: frame[PURCHASES_COL].div(frame[PURCHASES_COL].sum()))
        .sort_values(PURCHASES_COL, ascending=False)
    )
    media_labels = grouped[MEDIA_TYPE_COL].astype(str)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        name="Purchases",
        x=media_labels,
        y=grouped[PURCHASES_COL],
        marker_color=media_type_bar_colors(media_labels),
        secondary_y=False,
        showlegend=False,
    )
    fig.add_scatter(name="Purchase rate on launched campaign", x=media_labels, y=grouped["LaunchRate"], mode="lines+markers", line=dict(color=CPP_COLOR, width=3), secondary_y=True, showlegend=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        template="plotly_white",
        title_text="",
        showlegend=False,
    )
    fig.update_yaxes(title_text="Purchases", secondary_y=False)
    fig.update_yaxes(title_text="Purchase rate", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_content_spend_roas_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(MEDIA_TYPE_COL, as_index=False)[[SPEND_COL, SALES_COL]]
        .sum(numeric_only=True)
        .assign(ROAS=lambda frame: frame[SALES_COL].div(frame[SPEND_COL].replace(0, pd.NA)))
        .sort_values(SPEND_COL, ascending=False)
    )
    media_labels = grouped[MEDIA_TYPE_COL].astype(str)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        name="Amount spent",
        x=media_labels,
        y=grouped[SPEND_COL],
        marker_color=media_type_bar_colors(media_labels),
        secondary_y=False,
        showlegend=False,
    )
    fig.add_scatter(name="ROAS", x=media_labels, y=grouped["ROAS"], mode="lines+markers", line=dict(color=ROAS_COLOR, width=3), secondary_y=True, showlegend=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        template="plotly_white",
        title_text="",
        showlegend=False,
    )
    fig.update_yaxes(title_text="Amount spent (USD)", secondary_y=False)
    fig.update_yaxes(title_text="ROAS", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_content_cpc_ctr_chart(df: pd.DataFrame) -> go.Figure:
    grouped = (
        df.groupby(MEDIA_TYPE_COL, as_index=False)[[CPC_COL, CTR_COL]]
        .mean(numeric_only=True)
        .sort_values(CPC_COL, ascending=False)
    )
    media_labels = grouped[MEDIA_TYPE_COL].astype(str)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(
        name="CPC",
        x=media_labels,
        y=grouped[CPC_COL],
        marker_color=media_type_bar_colors(media_labels),
        secondary_y=False,
        showlegend=False,
    )
    fig.add_scatter(name="CTR", x=media_labels, y=grouped[CTR_COL], mode="lines+markers", line=dict(color=CTR_COLOR, width=3), secondary_y=True, showlegend=False)
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=300,
        template="plotly_white",
        title_text="",
        showlegend=False,
    )
    fig.update_yaxes(title_text="CPC", secondary_y=False)
    fig.update_yaxes(title_text="CTR", secondary_y=True)
    fig.update_yaxes(showgrid=True, secondary_y=False)
    fig.update_yaxes(showgrid=False, secondary_y=True)
    return compact_chart(fig)


def build_content_treemap(df: pd.DataFrame, leaf_col: str, title: str) -> go.Figure:
    grouped = (
        df.groupby([MEDIA_TYPE_COL, leaf_col], as_index=False)[PURCHASES_COL]
        .sum(numeric_only=True)
        .sort_values(PURCHASES_COL, ascending=False)
    )
    grouped = grouped[grouped[PURCHASES_COL].fillna(0) > 0].copy()
    if grouped.empty:
        return go.Figure()

    leaf_nodes = pd.DataFrame(
        {
            "id": grouped[MEDIA_TYPE_COL].astype(str) + "|" + grouped[leaf_col].astype(str),
            "label": grouped[leaf_col].astype(str),
            "parent": grouped[MEDIA_TYPE_COL].astype(str),
            "media_type": grouped[MEDIA_TYPE_COL].astype(str),
            "value": grouped[PURCHASES_COL].astype(float),
        }
    )
    root_nodes = grouped.groupby(MEDIA_TYPE_COL, as_index=False)[PURCHASES_COL].sum(numeric_only=True)
    root_nodes = root_nodes.rename(columns={MEDIA_TYPE_COL: "label", PURCHASES_COL: "value"})
    root_nodes["id"] = root_nodes["label"].astype(str)
    root_nodes["parent"] = ""
    root_nodes["media_type"] = root_nodes["label"].astype(str)

    tree = pd.concat([
        root_nodes[["id", "label", "parent", "media_type", "value"]],
        leaf_nodes[["id", "label", "parent", "media_type", "value"]],
    ], ignore_index=True)

    fig = go.Figure(go.Treemap(ids=tree["id"], labels=tree["label"], parents=tree["parent"], values=tree["value"], customdata=tree[["media_type"]], marker=dict(colorscale=THEME_TREEMAP_SCALE), branchvalues="total", hovertemplate="<b>%{label}</b><br>Purchases: %{value:,.0f}<extra></extra>"))
    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        height=340,
        template="plotly_white",
        title_text="",
    )
    return compact_chart(fig)


def render_kpis(filtered: pd.DataFrame) -> None:
    total_sales = filtered[SALES_COL].sum(skipna=True)
    total_spend = filtered[SPEND_COL].sum(skipna=True)
    total_purchases = filtered[PURCHASES_COL].sum(skipna=True)
    avg_cpp = total_spend / total_purchases if total_purchases else 0.0
    roas = total_sales / total_spend if total_spend else 0.0
    total_accounts = filtered[ACCOUNT_COL].nunique(dropna=True)

    kpi_cols = st.columns(6)
    kpis = [
        ("Revenue", money_short(total_sales)),
        ("Purchases", f"{int(total_purchases):,}"),
        ("Average CPP", f"${avg_cpp:,.0f}"),
        ("Amount spent", money_short(total_spend)),
        ("ROAS", format_ratio(roas)),
        ("Total Accounts", f"{total_accounts:,}"),
    ]

    for column, (title, value) in zip(kpi_cols, kpis, strict=False):
        with column:
            st.markdown(metric_card(title, value), unsafe_allow_html=True)


def render_overview(filtered: pd.DataFrame) -> None:
    if filtered.empty:
        st.info("No data for current filters.")
        return

    left_col, right_col = st.columns(2)
    with left_col:
        chart_title("Revenue & Amount Spent by Ad Account")
        st.plotly_chart(
            build_account_chart(filtered),
            width="stretch",
            key=ACCOUNT_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )

    with right_col:
        chart_title("Purchase & CPP by Country")
        st.plotly_chart(
            build_country_purchase_chart(filtered),
            width="stretch",
            key=COUNTRY_PURCHASE_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )

    left_col, right_col = st.columns(2, gap="small")
    with left_col:
        chart_title("Purchases & ROAS by Weekday")
        st.plotly_chart(
            build_weekday_roas_chart(filtered),
            width="stretch",
            key=WEEKDAY_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )

    with right_col:
        chart_title("Amount Spent & ROAS by Country")
        st.plotly_chart(
            build_country_spend_roas_chart(filtered),
            width="stretch",
            key=COUNTRY_SPEND_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )


def render_product(filtered: pd.DataFrame, product_metric: str = PRODUCT_COL, metric_label: str = "Product Types") -> None:
    product_ready = ensure_product_columns(filtered)
    if product_metric not in product_ready.columns:
        st.warning(f"Product dashboard needs Campaign name to parse product metrics. Column {product_metric} not found.")
        return

    summary = build_product_metric_summary(product_ready, product_metric)
    if summary.empty:
        st.info("No product data for current filters.")
        return

    classified, purchase_threshold, roas_threshold = classify_product_performance(summary)

    # Total products is the count of items in the grouped summary (each row = 1 product/metric)
    total_products = len(classified)
    total_purchases = float(classified[PURCHASES_COL].sum(skipna=True))
    total_revenue = float(classified[SALES_COL].sum(skipna=True))
    avg_roas = float(classified["ROAS"].mean(skipna=True)) if not classified.empty else 0.0
    scale_count = int((classified["Status"] == "Star").sum())
    optimize_count = int((classified["Status"] == "Optimize").sum())
    test_count = int((classified["Status"] == "Potentials").sum())
    cut_count = int((classified["Status"] == "Cut").sum())

    # KPI metrics are counted from raw parsed campaign taxonomy (not grouped summary).
    product_types = 0
    if PRODUCT_COL in product_ready.columns:
        product_types = int(
            product_ready[PRODUCT_COL]
            .astype("string")
            .str.upper()
            .replace("UNKNOWN", pd.NA)
            .dropna()
            .nunique()
        )

    product_ids = 0
    if PRODUCT_ID_COL in product_ready.columns:
        product_ids_series = product_ready[PRODUCT_ID_COL].astype("string").str.upper()
        valid_product_ids = product_ids_series[product_ids_series.str.match(r"^[A-Z]+\d+_[A-Z0-9]+$", na=False)]
        product_ids = int(valid_product_ids.nunique(dropna=True))

    niches = 0
    if NICHE_COL in product_ready.columns:
        niches = int(
            product_ready[NICHE_COL]
            .astype("string")
            .str.upper()
            .replace("UNKNOWN", pd.NA)
            .dropna()
            .nunique()
        )

    top_kpi_cols = st.columns(3)
    top_kpi_values = [
        ("Product Types", f"{product_types:,}"),
        ("Product IDs", f"{product_ids:,}"),
        ("Niches", f"{niches:,}"),
    ]
    for column, (title, value) in zip(top_kpi_cols, top_kpi_values, strict=False):
        with column:
            st.markdown(metric_card(title, value), unsafe_allow_html=True)

    # Status grid chart
    st.markdown(f'<div class="status-grid-title">{metric_label} Distribution by Status</div>', unsafe_allow_html=True)
    render_product_status_grid(scale_count, optimize_count, test_count, cut_count)

    st.markdown(f'<div class="product-table-title">Top {metric_label}</div>', unsafe_allow_html=True)

    with st.container(border=True, key="product_table_panel"):
        filter_label_col, filter_dropdown_col = st.columns([0.22, 0.78], gap="small")
        with filter_label_col:
            st.markdown(
                '<div style="font-weight: 700; color: #5a452d; margin-top: 0.35rem;">Filter by Status</div>',
                unsafe_allow_html=True,
            )
        with filter_dropdown_col:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", *PRODUCT_STATUS_ORDER],
                key=f"product_status_filter_{product_metric}",
                label_visibility="collapsed",
            )

        st.markdown('<div style="height: 0.35rem;"></div>', unsafe_allow_html=True)

        table_cols = [product_metric, PURCHASES_COL, "ROAS", "Average CPP", "Status"]
        table = classified[table_cols].copy()
        if status_filter != "All":
            table = table[table["Status"] == status_filter]
        table = table.reset_index(drop=True)

        col_rename_map = {
            "Average CPP": "CPP",
            product_metric: ("Product Type" if product_metric == PRODUCT_COL else
                           "Product ID" if product_metric == PRODUCT_ID_COL else
                           "Niche"),
        }
        table = table.rename(columns=col_rename_map)

        formatted_table = (
            table.style
            .format({
                "Purchases": "{:,.0f}",
                "CPP": "${:,.0f}",
                "ROAS": "{:.2f}",
            })
        )
        st.dataframe(formatted_table, width="stretch", height=560, selection_mode="multi-row", hide_index=True)


def render_content(filtered: pd.DataFrame) -> None:
    needed = [CTR_COL, CPC_COL, CPM_COL]
    if any(column not in filtered.columns for column in needed):
        st.warning("Content dashboard needs CTR, CPC, and CPM columns.")
        return

    content_ready = ensure_product_columns(filtered)
    if MEDIA_TYPE_COL not in content_ready.columns:
        st.warning("Content dashboard needs Campaign name to derive media type.")
        return

    if filtered.empty:
        st.info("No data for current filters.")
        return

    selected_media_values = set(selected_values_from_chart_key(CONTENT_MEDIA_PURCHASE_CHART_KEY))
    selected_media_values |= set(selected_values_from_chart_key(CONTENT_SPEND_ROAS_CHART_KEY))
    selected_media_values |= set(selected_values_from_chart_key(CONTENT_CPC_CTR_CHART_KEY))
    selected_media_values |= set(selected_values_from_chart_key(CONTENT_NICHE_TREEMAP_KEY))
    selected_media_values |= set(selected_values_from_chart_key(CONTENT_PRODUCT_TREEMAP_KEY))
    if selected_media_values:
        content_ready = content_ready[content_ready[MEDIA_TYPE_COL].astype(str).isin(selected_media_values)]

    if content_ready.empty:
        st.info("No data for the selected media type chart interaction.")
        return

    # KPI cards by media type purchases
    media_summary = content_ready.groupby(MEDIA_TYPE_COL, as_index=False)[PURCHASES_COL].sum(numeric_only=True)
    media_summary = media_summary.sort_values(PURCHASES_COL, ascending=False)

    media_cards = st.columns(3)
    for column, (_, row) in zip(media_cards, media_summary.iterrows(), strict=False):
        with column:
            st.markdown(metric_card(str(row[MEDIA_TYPE_COL]), f"{int(row[PURCHASES_COL]):,}"), unsafe_allow_html=True)

    st.write("")

    # Top row: three column charts
    top_col1, top_col2, top_col3 = st.columns(3, gap="small")
    with top_col1:
        chart_title("Purchase Rate by Media Type")
        st.plotly_chart(
            build_content_media_purchase_chart(content_ready),
            width="stretch",
            key=CONTENT_MEDIA_PURCHASE_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )
    with top_col2:
        chart_title("Amount Spent & ROAS by Media Type")
        st.plotly_chart(
            build_content_spend_roas_chart(content_ready),
            width="stretch",
            key=CONTENT_SPEND_ROAS_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )
    with top_col3:
        chart_title("CPC & CTR by Media Type")
        st.plotly_chart(
            build_content_cpc_ctr_chart(content_ready),
            width="stretch",
            key=CONTENT_CPC_CTR_CHART_KEY,
            on_select="rerun",
            selection_mode="points",
            config={"displayModeBar": False},
        )

    # Bottom row: two treemaps
    bottom_col1, bottom_col2 = st.columns(2, gap="small", vertical_alignment="center")
    with bottom_col1:
        with st.container(key="content_treemap_left"):
            t1 = build_content_treemap(content_ready, NICHE_COL, "Purchases by Media Type & Niche")
            if t1.data:
                chart_title("Purchases by Media Type & Niche")
                st.plotly_chart(
                    t1,
                    width="stretch",
                    key=CONTENT_NICHE_TREEMAP_KEY,
                    on_select="rerun",
                    selection_mode="points",
                    config={"displayModeBar": False},
                )
    with bottom_col2:
        with st.container(key="content_treemap_right"):
            t2 = build_content_treemap(content_ready, PRODUCT_COL, "Purchases by Media Type & Product")
            if t2.data:
                chart_title("Purchases by Media Type & Product")
                st.plotly_chart(
                    t2,
                    width="stretch",
                    key=CONTENT_PRODUCT_TREEMAP_KEY,
                    on_select="rerun",
                    selection_mode="points",
                    config={"displayModeBar": False},
                )


with st.sidebar:
    logo_data_uri = load_logo_data_uri(str(LOGO_PATH))
    if logo_data_uri:
        st.markdown(
            f"""
            <div class="brand-panel">
                <div class="brand-logo-wrap">
                    <img src="{logo_data_uri}" alt="Almagems" class="brand-logo" />
                </div>
                <div class="brand-subtitle">Monthly Report for Almagems</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="brand-panel">
                <div class="brand-name">Almagems</div>
                <div class="brand-subtitle">Monthly Report for Almagems</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    upload = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], help="Upload your report to view the dashboard.")

    if upload is None:
        st.info("Upload a CSV or Excel file to load the dashboard.")
        st.stop()

    df = load_uploaded_data(upload.getvalue(), upload.name)
    source_name = upload.name

    df = ensure_product_columns(df)

    st.markdown("### Filters")
    dashboard_view = st.radio("Navigate", ["Overview", "Product", "Content"], index=0)
    
    # Product metric selector (only show for Product view)
    product_metric = PRODUCT_COL  # default value
    selected_metric_label = "Product Types"  # default label
    metric_options = [
        ("Product Types", PRODUCT_COL),
        ("Product IDs", PRODUCT_ID_COL),
        ("Niches", NICHE_COL),
    ]
    if dashboard_view == "Product":
        selected_metric_label = st.radio(
            "Group By",
            [label for label, _ in metric_options],
            index=0,
        )
        product_metric = next(col for label, col in metric_options if label == selected_metric_label)

    if st.button("Reset view", key="reset_view"):
        clear_chart_selection_keys([
            ACCOUNT_CHART_KEY,
            COUNTRY_PURCHASE_CHART_KEY,
            WEEKDAY_CHART_KEY,
            COUNTRY_SPEND_CHART_KEY,
            CONTENT_MEDIA_PURCHASE_CHART_KEY,
            CONTENT_SPEND_ROAS_CHART_KEY,
            CONTENT_CPC_CTR_CHART_KEY,
            CONTENT_NICHE_TREEMAP_KEY,
            CONTENT_PRODUCT_TREEMAP_KEY,
        ])
        st.rerun()
    
    account_options = build_options(df[ACCOUNT_COL])
    country_options = build_options(df[COUNTRY_COL], COUNTRY_ORDER)
    weekday_options = WEEKDAY_ORDER
    media_type_options = build_options(df[MEDIA_TYPE_COL]) if MEDIA_TYPE_COL in df.columns else []

    if "country_filter" not in st.session_state:
        initial_countries = [
            country for country in OVERVIEW_DEFAULT_COUNTRIES if country in country_options
        ]
        st.session_state["country_filter"] = initial_countries or country_options

    selected_accounts = st.multiselect("Account name", account_options, default=account_options)
    selected_weekdays = st.multiselect("Weekday", weekday_options, default=weekday_options)
    selected_countries = st.multiselect("Country", country_options, key="country_filter")
    selected_media_types = st.multiselect("Media type", media_type_options, default=media_type_options)

filtered = apply_filters(df, selected_accounts, selected_countries, selected_weekdays, selected_media_types)

if dashboard_view == "Overview":
    account_chart_selection = selected_values_from_chart_key(ACCOUNT_CHART_KEY)
    country_purchase_selection = selected_values_from_chart_key(COUNTRY_PURCHASE_CHART_KEY)
    weekday_chart_selection = selected_values_from_chart_key(WEEKDAY_CHART_KEY)
    country_spend_selection = selected_values_from_chart_key(COUNTRY_SPEND_CHART_KEY)

    active_accounts = selected_accounts
    if account_chart_selection:
        active_accounts = [value for value in selected_accounts if value in set(account_chart_selection)]

    active_countries = selected_countries
    selected_country_values = set(country_purchase_selection) | set(country_spend_selection)
    if selected_country_values:
        active_countries = [value for value in selected_countries if value in selected_country_values]

    active_weekdays = selected_weekdays
    if weekday_chart_selection:
        active_weekdays = [value for value in selected_weekdays if value in set(weekday_chart_selection)]

    filtered = apply_filters(df, active_accounts, active_countries, active_weekdays, selected_media_types)

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f4eee3 0%, #f9f4eb 18%, #fbf8f1 100%);
        }
        .block-container {
            padding-top: 3.2rem;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #efe5d3 0%, #f6efdf 100%);
        }
        .brand-panel {
            padding: 1rem 1rem 1.25rem 1rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,252,246,0.97), rgba(244,234,220,0.97));
            border: 1px solid rgba(153, 120, 75, 0.22);
            box-shadow: 0 10px 30px rgba(126, 98, 58, 0.12);
            margin-bottom: 1rem;
        }
        .brand-name {
            font-size: 2.7rem;
            line-height: 1;
            font-weight: 900;
            letter-spacing: -0.04em;
            color: #6d4f2f;
        }
        .brand-logo-wrap {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.35rem;
        }
        .brand-logo {
            width: 82%;
            max-width: 160px;
            height: auto;
            object-fit: contain;
        }
        .brand-subtitle {
            margin-top: 0.35rem;
            color: #6a5a45;
            font-size: 0.9rem;
            text-align: center;
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid rgba(146, 115, 76, 0.22);
            border-radius: 18px;
            padding: 1rem 0.9rem;
            box-shadow: 0 8px 24px rgba(122, 95, 62, 0.09);
            text-align: center;
            min-height: 92px;
        }
        .metric-title {
            font-size: 0.9rem;
            font-weight: 700;
            color: #7a6242;
            margin-bottom: 0.45rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #4f3b24;
            line-height: 1.05;
        }
        .insight-panel {
            background: #ffffff;
            border: 1px solid rgba(146, 115, 76, 0.22);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 24px rgba(122, 95, 62, 0.09);
            margin: 0.15rem 0 1rem 0;
        }
        .insight-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #4f3b24;
            margin-bottom: 0.4rem;
        }
        .insight-list {
            margin: 0;
            padding-left: 1.15rem;
            color: #5a452d;
        }
        .insight-list li {
            margin-bottom: 0.35rem;
        }
        .viz-title {
            font-size: 2rem;
            font-weight: 800;
            color: #4f3b24;
            line-height: 1.2;
            margin: 0.2rem 0 0.65rem 0;
        }
        h1 {
            font-size: 2rem !important;
            line-height: 1.15 !important;
            margin: 0.12rem 0 0.52rem 0 !important;
            padding: 0 !important;
        }
        .chart-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #5a452d;
            margin: 0.55rem 0 0.25rem 0;
            width: 100%;
            text-align: center;
        }
        .status-grid-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #5a452d;
            margin: 0.55rem 0 0.12rem 0;
            width: 100%;
            text-align: center;
        }
        .product-table-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #5a452d;
            margin: 0.55rem 0 0.08rem 0;
            width: 100%;
            text-align: center;
        }
        .stPlotlyChart {
            background: #ffffff;
            border: 1px solid rgba(146, 115, 76, 0.22);
            border-radius: 10pt;
            padding: 0.18rem;
            overflow: hidden;
        }
        .status-grid-wrapper {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            margin: 0.15rem 0 1rem 0;
            padding: 1.5rem;
            background: #ffffff;
            border: 2px solid rgba(146, 115, 76, 0.3);
            border-radius: 12px;
        }
        .status-grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
            padding: 0;
            background: transparent;
            border: none;
        }
        .status-grid-row {
            display: contents;
        }
        .status-grid-cell {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 110px;
            border: 3px solid;
            border-radius: 8px;
            padding: 1.2rem;
        }
        .status-grid-label {
            font-size: 0.88rem;
            font-weight: 700;
            color: #4f3b24;
            margin-bottom: 0.45rem;
        }
        .status-grid-number {
            font-size: 1.9rem;
            font-weight: 800;
            color: #4f3b24;
        }
        .st-key-product_table_panel {
            background-color: #ffffff !important;
            border: 1px solid rgba(146, 115, 76, 0.22) !important;
            border-radius: 12px;
            padding: 0.95rem !important;
            overflow: hidden;
        }
        .st-key-product_table_panel [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
        }
        .st-key-content_treemap_left .stPlotlyChart,
        .st-key-content_treemap_right .stPlotlyChart {
            min-height: 340px;
            overflow: hidden !important;
        }
        .st-key-content_treemap_left [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-content_treemap_right [data-testid="stVerticalBlockBorderWrapper"] {
            overflow: visible !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Extract month/year from data and format title
month_year = get_report_month_year(df)
if dashboard_view == "Product":
    dashboard_title = f"Almagems - {month_year} - {dashboard_view} ({selected_metric_label})"
else:
    dashboard_title = f"Almagems - {month_year} - {dashboard_view}"
st.title(dashboard_title)
st.write("")

if dashboard_view != "Product" and dashboard_view != "Content":
    render_kpis(filtered)
    st.write("")

if dashboard_view == "Overview":
    render_overview(filtered)
elif dashboard_view == "Product":
    render_product(filtered, product_metric, selected_metric_label)
else:
    render_content(filtered)

with st.expander("Show filtered data"):
    st.dataframe(
        filtered[[ACCOUNT_COL, COUNTRY_COL, DAY_COL, SPEND_COL, SALES_COL, PURCHASES_COL, CPP_COL]].head(200),
        width="stretch",
    )

st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="AllAccountReport-Mar2026-filtered.csv",
    mime="text/csv",
)