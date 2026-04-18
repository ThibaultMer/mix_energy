"""
Shared scaffolding for the MiX-ENERGIE Streamlit dashboard.

This module centralizes the page configuration, theme CSS, data loading,
and session-state handling so the homepage and multipage views can reuse the
same runtime context.
"""

from __future__ import annotations

import base64
from datetime import date, timedelta
from pathlib import Path

import os
import pandas as pd
import streamlit as st
import json

import plotly.express as px

from data_api_client import FastAPIClient

APP_PAGE_TITLE = "PROJET MiX-ENERGIE"
APP_PAGE_ICON = "⚡"
APP_LAYOUT = "wide"
APP_SIDEBAR_STATE = "expanded"


SOURCE_COLUMNS = {
    "Fioul": "fioul",
    "Charbon": "charbon",
    "Gaz": "gaz",
    "Nucleaire": "nucleaire",
    "Eolien": "eolien",
    "Solaire": "solaire",
    "Hydraulique": "hydraulique",
    "Pompage": "pompage",
    "Bioenergies": "bioenergies",
}

COLORS = {
    "Fioul": "#ff9822",
    "Charbon": "#030100",
    "Gaz": "#ff7043",
    "Nucleaire": "#00e0ff",
    "Eolien": "#69ff69",
    "Solaire": "#ffd600",
    "Hydraulique": "#c207fc",
    "Pompage": "#82b1ff",
    "Bioenergies": "#05f3cb",
}

REGIONS_DICT = {
    "53": "Bretagne",
    "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes",
    "27": "Bourgogne-Franche-Comté",
    "44": "Grand Est",
    "75": "Nouvelle-Aquitaine",
    "32": "Hauts-de-France",
    "11": "Île-de-France",
    "24": "Centre-Val de Loire",
    "28": "Normandie",
    "52": "Pays de la Loire",
    "93": "Provence-Alpes-Côte d'Azur",
}


def configure_page() -> None:
    st.set_page_config(
        page_title=APP_PAGE_TITLE,
        page_icon=APP_PAGE_ICON,
        layout=APP_LAYOUT,
        initial_sidebar_state=APP_SIDEBAR_STATE,
    )


def get_base64_image(path: Path) -> str:
    if path.exists():
        with open(path, "rb") as file_handle:
            return base64.b64encode(file_handle.read()).decode()
    return ""


def build_bg_css() -> str:
    return """
    .bg-layer {
        position: fixed;
        inset: 0;
        background: linear-gradient(135deg, #0a1628 0%, #0d2137 50%, #0a1628 100%);
        z-index: 0;
    }
    """


def apply_global_style(*, use_background_image: bool = True) -> None:
    if use_background_image:
        bg_css = build_bg_css()
        overlay_bg = "rgba(255, 255, 255, 0.06)"
        body_color = "#e8f4ff"
        app_background = "transparent"
    else:
        bg_css = """
    .bg-layer {
        position: fixed;
        inset: 0;
        background: #ffffff;
        z-index: 0;
    }
    """
        overlay_bg = "transparent"
        body_color = "#111111"
        app_background = "#ffffff"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

/* Background */
{bg_css}

/* Keep decorative layers from intercepting wheel/touch events */
.bg-layer,
.overlay-layer {{
    pointer-events: none;
}}

/* Overlay tint */
.overlay-layer {{
    position: fixed;
    inset: 0;
    background: {overlay_bg};
    z-index: 1;
}}

/* All Streamlit content above bg */
[data-testid="stAppViewContainer"] > * {{
    position: relative;
    z-index: 2;
}}
[data-testid="stAppViewContainer"] {{
    background: {app_background} !important;
    overflow-y: auto;
}}
[data-testid="stHeader"] {{
    background: transparent !important;
    z-index: 3;
}}
[data-testid="stSidebar"] {{
    background: rgba(8, 20, 45, 0.88) !important;
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(0, 220, 255, 0.18);
    z-index: 4;
    min-width: 440px !important;
}}

/* Body font */
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif;
    color: {body_color};
}}

/*/* Main container centering */
.main .block-container {{
    max-width: 860px;
    margin: 0 auto;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}}

/* Page titles (st.title) */
h1 {{
    text-shadow:
        -1px -1px 0 #000000,
        1px -1px 0 #000000,
        -1px 1px 0 #000000,
        1px 1px 0 #000000,
        -1.5px 0 0 #000000,
        1.5px 0 0 #000000,
        0 -1.5px 0 #000000,
        0 1.5px 0 #000000,
        0 0 30px rgba(0, 210, 255, 0.5),
        0 0 60px rgba(0, 150, 255, 0.2) !important;
}}

/* ── HERO HEADER ── */
.hero-header {{
    text-align: center;
    padding: 2.4rem 1rem 1.6rem;
    margin-bottom: 0.5rem;
}}
.hero-title {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 3rem !important;
    font-weight: 900;
    letter-spacing: 0.08em;
    color: #ffffff;
    text-shadow:
        -1px -1px 0 #000000,
        1px -1px 0 #000000,
        -1px 1px 0 #000000,
        1px 1px 0 #000000,
        -1.5px 0 0 #000000,
        1.5px 0 0 #000000,
        0 -1.5px 0 #000000,
        0 1.5px 0 #000000,
        0 0 30px rgba(0, 210, 255, 0.5),
        0 0 60px rgba(0, 150, 255, 0.2);
    margin: 0;
    line-height: 1.2;
}}
.hero-subtitle {{
    font-size: 2rem !important;
    font-weight: 700;
    color: #ffffff;
    margin-top: 0.8rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    text-shadow:
        -1px -1px 0 #000000,
        1px -1px 0 #000000,
        -1px 1px 0 #000000,
        1px 1px 0 #000000,
        -1.5px 0 0 #000000,
        1.5px 0 0 #000000,
        0 -1.5px 0 #000000,
        0 1.5px 0 #000000;
}}
.hero-icon {{
    font-size: 5.6rem;
    display: block;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 0 24px rgba(0, 220, 255, 0.9));
}}

/* ── KPI STRIP ── */
.kpi-strip {{
    display: flex;
    justify-content: center;
    gap: 1.2rem;
    flex-wrap: wrap;
    margin: 1rem auto 2rem;
}}
.kpi-card {{
    background: rgba(0, 30, 65, 0.72);
    border: 1px solid rgba(0, 200, 255, 0.22);
    border-radius: 10px;
    padding: 0.75rem 1.4rem;
    text-align: center;
    backdrop-filter: blur(8px);
    min-width: 130px;
    box-shadow: 0 4px 20px rgba(0, 150, 255, 0.12);
    transition: border-color 0.2s;
}}
.kpi-card:hover {{ border-color: rgba(0, 220, 255, 0.55); }}
.kpi-value {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #00e0ff;
    text-shadow: 0 0 10px rgba(0, 220, 255, 0.6);
}}
.kpi-label {{
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(160, 210, 255, 0.7);
    margin-top: 0.15rem;
}}

/* ── CHART CARDS ── */
.chart-card {{
    background: rgba(5, 18, 45, 0.78);
    border: 1px solid rgba(0, 180, 255, 0.2);
    border-radius: 14px;
    padding: 1.4rem 1.6rem 1rem;
    margin-bottom: 1.8rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 100, 200, 0.14);
    transition: border-color 0.25s, box-shadow 0.25s;
}}
.chart-card:hover {{
    border-color: rgba(0, 220, 255, 0.4);
    box-shadow: 0 12px 40px rgba(0, 160, 255, 0.22);
}}
.chart-title {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #7dd6ff;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.chart-desc {{
    font-size: 1.1rem;
    color: rgba(160, 210, 255, 0.65);
    margin-bottom: 0.9rem;
    line-height: 1.5;
}}

/* ── SIDEBAR ── */
.sidebar-section {{
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(0, 220, 255, 0.6);
    margin: 1.2rem 0 0.4rem;
    border-bottom: 1px solid rgba(0, 180, 255, 0.18);
    padding-bottom: 0.25rem;
}}

/* Sidebar text styling */
[data-testid="stSidebar"] {{
    color: #ffffff !important;
}}

[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] span {{
    color: #ffffff !important;
}}

/* Sidebar title centering */
[data-testid="stSidebar"] h3 {{
    text-align: center !important;
}}

/* Sidebar description centering */
[data-testid="stSidebar"] h3 + p {{
    text-align: center !important;
}}

/* Center all markdown paragraphs after icon but before separator */
[data-testid="stSidebar"] > div:first-child p {{
    text-align: center !important;
}}

/* Sidebar page links styling */
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] a {{
    color: #ffffff !important;
}}

/* Sidebar icon centering */
[data-testid="stSidebar"] .hero-icon {{
    text-align: center !important;
    margin-left: auto !important;
    margin-right: auto !important;
    width: fit-content !important;
}}

/* Streamlit widget overrides */
[data-testid="stSelectbox"] label,
[data-testid="stMultiSelect"] label,
[data-testid="stSlider"] label {{
    font-size: 0.78rem !important;
    color: rgba(160, 210, 255, 0.8) !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
div[data-baseweb="select"] {{
    background: rgba(0, 20, 50, 0.6) !important;
    border-color: rgba(0, 180, 255, 0.3) !important;
}}
[data-testid="stSidebar"] div[data-baseweb="select"] svg {{
    fill: #c8e6ff !important;
    color: #c8e6ff !important;
}}

/* Date input styling for sidebar */
[data-testid="stSidebar"] input[type="date"],
[data-testid="stSidebar"] input {{
    color: #000000 !important;
}}

/* Divider */
hr {{
    border-color: rgba(0, 180, 255, 0.15) !important;
    margin: 0.5rem 0 1.5rem !important;
}}

/* Footer */
.footer {{
    text-align: center;
    font-size: 1rem;
    color: rgba(250, 250, 250, 1);
    padding: 1.5rem 0 0.5rem;
    letter-spacing: 0.1em;
}}

/* Plotly chart titles with subtle black outline */
[data-testid="plotly-graph"] svg text {{
    paint-order: stroke fill;
    stroke: #000000;
    stroke-width: 0.3px;
    stroke-linecap: butt;
    stroke-linejoin: miter;
}}
</style>
<div class="bg-layer"></div>
<div class="overlay-layer"></div>
""",
        unsafe_allow_html=True,
    )


TABLES = {
    "table1": "nat_cons_agre_j",
    "table2": "nat_tr_agre_j",
    "table3": "reg_cons_agre_j",
    "table4": "reg_tr_agre_j",
    "table5": "kpi",
}


def _default_region() -> str:
    return (
        "Île-de-France"
        if "Île-de-France" in REGIONS_DICT.values()
        else sorted(REGIONS_DICT.values())[0]
    )


def _year_window_current_and_previous() -> tuple[date, date]:
    today = date.today()
    return date(today.year - 1, 1, 1), today


def _current_month_window() -> tuple[date, date]:
    today = date.today()
    return date(today.year, today.month, 1), today


def _rolling_last_30_days_window() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=29), today


@st.cache_data(ttl=3600, show_spinner="Connexion à FastAPI...")
def _get_api_health() -> dict:
    return FastAPIClient.from_environment().health()


@st.cache_data(ttl=3600)
def _get_api_table_columns(table_name: str) -> list[dict]:
    return FastAPIClient.from_environment().get_table_columns(table_name)


@st.cache_data(
    ttl=3600, show_spinner="Chargement des données nationales historiques..."
)
def load_national_historical_data() -> pd.DataFrame:
    client = FastAPIClient.from_environment()
    start_date, end_date = _year_window_current_and_previous()
    rows = client.load_rows_for_date_range(
        TABLES["table1"],
        start_date=start_date,
        end_date=end_date,
    )
    return _normalize_dataframe(pd.DataFrame(rows), table_name=TABLES["table1"])


@st.cache_data(ttl=300, show_spinner="Chargement des données nationales temps réel...")
def load_national_realtime_data() -> pd.DataFrame:
    client = FastAPIClient.from_environment()
    start_date, end_date = _rolling_last_30_days_window()
    rows = client.load_rows_for_date_range(
        TABLES["table2"],
        start_date=start_date,
        end_date=end_date,
    )
    return _normalize_dataframe(pd.DataFrame(rows), table_name=TABLES["table2"])


@st.cache_data(
    ttl=3600, show_spinner="Chargement des données régionales historiques..."
)
def load_regional_historical_data(region: str) -> pd.DataFrame:
    client = FastAPIClient.from_environment()
    start_date, end_date = _year_window_current_and_previous()
    region_field = _detect_region_field(TABLES["table3"])
    rows = client.load_rows_for_date_range(
        TABLES["table3"],
        start_date=start_date,
        end_date=end_date,
        extra_filters=[{"field": region_field, "operator": "eq", "value": region}],
    )
    return _normalize_dataframe(pd.DataFrame(rows), table_name=TABLES["table3"])


@st.cache_data(ttl=300, show_spinner="Chargement des données régionales temps réel...")
def load_regional_realtime_data(region: str) -> pd.DataFrame:
    client = FastAPIClient.from_environment()
    start_date, end_date = _current_month_window()
    region_field = _detect_region_field(TABLES["table4"])
    rows = client.load_rows_for_date_range(
        TABLES["table4"],
        start_date=start_date,
        end_date=end_date,
        extra_filters=[{"field": region_field, "operator": "eq", "value": region}],
    )
    return _normalize_dataframe(pd.DataFrame(rows), table_name=TABLES["table4"])


@st.cache_data(ttl=300, show_spinner="Chargement des données moyenne du mois...")
def load_kpi_data() -> pd.DataFrame:
    client = FastAPIClient.from_environment()
    start_date, end_date = _current_month_window()
    rows = client.load_rows_for_date_range(
        TABLES["table5"], start_date=start_date, end_date=end_date
    )
    return _normalize_dataframe(pd.DataFrame(rows), table_name=TABLES["table5"])


@st.cache_data(ttl=300, show_spinner="Chargement des données position...")
def read_geojson():
    current_path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_path, "regions.geojson"), "r") as reg_geo:
        regions = json.load(reg_geo)

    return regions


@st.cache_data(ttl=300, show_spinner="Calcul de prédiction nationale...")
def get_next_conso_nat():
    result = FastAPIClient.from_environment().predict_national()
    return result


@st.cache_data(ttl=300, show_spinner="Calcul de prédiction régionale...")
def get_next_conso_reg(insee_code: int):
    result = FastAPIClient.from_environment().prediction_region(insee_code)
    return result


def clear_realtime_cache() -> None:
    load_national_realtime_data.clear()
    load_regional_realtime_data.clear()


def _normalize_dataframe(frame: pd.DataFrame, *, table_name: str) -> pd.DataFrame:
    if frame.empty:
        return frame

    if "mois" not in frame.columns and "date" in frame.columns:
        frame = frame.rename(columns={"date": "mois"})

    if "mois" in frame.columns:
        frame["mois"] = pd.to_datetime(
            frame["mois"], utc=True, errors="coerce"
        ).dt.tz_convert(None)

    if (
        table_name.startswith("reg_")
        and "libelle_region" not in frame.columns
        and "region" in frame.columns
    ):
        frame["libelle_region"] = frame["region"]

    return frame


def _detect_region_field(table_name: str) -> str:
    columns = {column.get("name") for column in _get_api_table_columns(table_name)}
    if "libelle_region" in columns:
        return "libelle_region"
    return "region"


def get_region_options() -> list[str]:
    return sorted(REGIONS_DICT.values())


def get_energy_types() -> list[str]:
    return list(SOURCE_COLUMNS.keys())


def melt_source_values(
    frame: pd.DataFrame, *, region_column: str | None = None
) -> pd.DataFrame:
    source_frame = frame.copy()
    source_frame["mois"] = pd.to_datetime(source_frame["mois"], utc=True).dt.tz_convert(
        None
    )
    id_columns = ["mois"]
    if region_column:
        id_columns.append(region_column)
    if "taux_co2" in source_frame.columns:
        id_columns.append("taux_co2")
    source_value_columns = [
        column for column in SOURCE_COLUMNS.values() if column in source_frame.columns
    ]
    melted = source_frame.melt(
        id_vars=id_columns,
        value_vars=source_value_columns,
        var_name="source_column",
        value_name="value",
    )
    inverse_sources = {column: label for label, column in SOURCE_COLUMNS.items()}
    melted["EnergyType"] = melted["source_column"].map(inverse_sources)
    return melted


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    color = hex_color.lstrip("#")
    if len(color) == 3:
        color = "".join(character * 2 for character in color)
    red, green, blue = (int(color[index : index + 2], 16) for index in (0, 2, 4))
    return f"rgba({red},{green},{blue},{alpha})"


def styled_axis(title: str = "") -> dict:
    return {
        "title": {"text": title, "font": {"size": 11, "color": "#c8e6ff"}},
        "gridcolor": "rgba(255,255,255,0.18)",
        "zerolinecolor": "rgba(255,255,255,0.6)",
        "tickfont": {"size": 10, "color": "#c8e6ff"},
        "linecolor": "#ffffff",
    }


def get_realtime_numeric_columns(
    frame: pd.DataFrame, *, extra_excluded: set[str] | None = None
) -> list[str]:
    excluded_columns = {
        "row",
        "perimetre",
        "nature",
        "date",
        "mois",
        "year",
        "month",
        "day",
        "taux_co2",
        "annee",
        "année",
        "jour",
    }
    if extra_excluded:
        excluded_columns.update(extra_excluded)

    excluded_lower = {column.lower() for column in excluded_columns}
    return [
        column
        for column in frame.columns
        if column.lower() not in excluded_lower
        and pd.api.types.is_numeric_dtype(frame[column])
    ]


def apply_widget_text_style(
    *, color: str = "#c8e6ff", font_size: str | None = None
) -> None:
    font_size_rule = f"font-size: {font_size} !important;" if font_size else ""
    st.markdown(
        f"""
<style>
/* Labels for local chart controls */
div[data-testid="stWidgetLabel"] p,
div[data-testid="stWidgetLabel"] span,
label[data-testid="stWidgetLabel"] {{
    color: {color} !important;
    {font_size_rule}
}}

/* Selected values and dropdown options text */
div[data-baseweb="select"] *,
div[data-baseweb="select"] span,
div[data-baseweb="popover"] *,
ul[role="listbox"] *,
li[role="option"] * {{
    color: #0b1f33 !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#c8e6ff", size=12),
    margin=dict(l=10, r=10, t=30, b=40),
    legend=dict(
        bgcolor="rgba(0,15,40,0.65)",
        bordercolor="rgba(0,180,255,0.2)",
        borderwidth=1,
        font=dict(size=11),
    ),
)


def _build_context(page_df: pd.DataFrame, *, table_key: str) -> dict:
    return {
        "all_dfs": {table_key: page_df},
        "REGIONS": get_region_options(),
        "ENERGY_TYPES": get_energy_types(),
        "COLORS": COLORS,
        "BASE_LAYOUT": BASE_LAYOUT,
        "styled_axis": styled_axis,
        "hex_to_rgba": hex_to_rgba,
    }


def get_national_historical_context() -> dict:
    try:
        _get_api_health()
        df_nat_cons_agre_j = load_national_historical_data()
    except Exception as exc:
        st.error(f"Erreur de chargement FastAPI (national historique): {exc}")
        st.stop()
    context = _build_context(df_nat_cons_agre_j, table_key="table1")
    context["df_nat_cons_agre_j"] = df_nat_cons_agre_j
    return context


def get_national_realtime_context() -> dict:
    try:
        _get_api_health()
        df_nat_tr_agre_j = load_national_realtime_data()
    except Exception as exc:
        st.error(f"Erreur de chargement FastAPI (national temps reel): {exc}")
        st.stop()
    context = _build_context(df_nat_tr_agre_j, table_key="table2")
    context["df_nat_tr_agre_j"] = df_nat_tr_agre_j
    return context


def get_regional_historical_context(region: str | None = None) -> dict:
    selected_region = region or _default_region()
    try:
        _get_api_health()
        df_reg_cons_agre_j = load_regional_historical_data(selected_region)
    except Exception as exc:
        st.error(f"Erreur de chargement FastAPI (regional historique): {exc}")
        st.stop()
    context = _build_context(df_reg_cons_agre_j, table_key="table3")
    context["df_reg_cons_agre_j"] = df_reg_cons_agre_j
    context["selected_region"] = selected_region

    if "geopos" not in context.keys():
        context["geopos"] = read_geojson()

    return context


def get_regional_realtime_context(region: str | None = None) -> dict:
    selected_region = region or _default_region()
    try:
        _get_api_health()
        df_reg_tr_agre_j = load_regional_realtime_data(selected_region)
    except Exception as exc:
        st.error(f"Erreur de chargement FastAPI (regional temps reel): {exc}")
        st.stop()
    context = _build_context(df_reg_tr_agre_j, table_key="table4")
    context["df_reg_tr_agre_j"] = df_reg_tr_agre_j
    context["selected_region"] = selected_region

    if "geopos" not in context.keys():
        context["geopos"] = read_geojson()

    return context


def ___get_choremap_df(df_regions: pd.Dataframe) -> pd.Dataframe:
    df_reduced = df_regions.groupby(
        by=["code_insee_region", "date", "libelle_region"], as_index=False
    )["consommation"].sum()
    df_reduced["date"].max()
    df_reduced = df_reduced[df_reduced.date == df_reduced.date.max()]
    df_last = df_reduced.drop(columns=["date"])
    df_last = df_last.rename(columns={"code_insee_region": "code"})
    return df_last


def plot_heatmap(df_regions: pd.DataFrame, context: dict, range_color=tuple):
    df_rebuilt = ___get_choremap_df(df_regions)
    regions = context["geopos"]

    fig = px.choropleth_map(
        df_rebuilt,
        geojson=regions,
        locations="code",
        color="consommation",
        featureidkey="properties.code",
        color_continuous_scale="Hot",
        range_color=range_color,
        map_style="carto-positron",
        zoom=4,
        # center = {"lat": 43.327408, "lon": -1.032999}, Saint-Palais
        # center = {"lat": 48.866667, "lon": 2.333333}, Paris
        center={
            "lat": 47.0,
            "lon": 1.909000,
        },  # Autour d'Orléans (lon: 47.902500, lat: 1.909000)
        opacity=0.5,
        hover_data=["libelle_region", "consommation"],
        labels={"consommation": "consommation energie"},
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<span class="hero-icon">⚡</span>', unsafe_allow_html=True)
        st.markdown("### * PROJET MiX-ENERGIE - FRANCE *")
        st.markdown(
            "* Analyse de la Production d'Electricité, de son impact carbone et de son coût à travers les régions françaises."
        )


def render_page1_sidebar_filters(
    df: pd.DataFrame, y_columns: list[str], default_y: list[str]
) -> tuple:
    """Render page 1 filters in sidebar"""
    min_date = df["plot_date"].min().date()
    max_date = df["plot_date"].max().date()

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-section">🔍 Filtres du graphique</div>',
            unsafe_allow_html=True,
        )

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input(
                "Date debut",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="nh_start_date",
            )
        with date_col2:
            end_date = st.date_input(
                "Date fin",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="nh_end_date",
            )

        selected_y = st.multiselect(
            "Sources d'energies:",
            y_columns,
            default=default_y,
            key="energy_y_select",
        )

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.68rem;color:rgba(120,180,230,0.45);line-height:1.6;'>"
            "Data: FastAPI backend · Live dashboard<br>© 2026 Electricity Dashboard</div>",
            unsafe_allow_html=True,
        )

    return start_date, end_date, selected_y


def render_page2_sidebar_filters(
    y_columns: list[str], default_y: list[str]
) -> list[str]:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-section">🔍 Filtres du graphique</div>',
            unsafe_allow_html=True,
        )
        selected_y = st.multiselect(
            "Sources d'energies:",
            y_columns,
            default=default_y,
            key="nrt_energy_y_select",
        )
    return selected_y
