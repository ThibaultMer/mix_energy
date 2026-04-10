"""
Page 1: Vision national historique et consolidée des données de production d'électricité en France

"""

# Import necessary libraries
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dashboard_share import (
    BASE_LAYOUT,
    COLORS,
    SOURCE_COLUMNS,
    apply_widget_text_style,
    apply_global_style,
    configure_page,
    get_national_historical_context,
    render_sidebar,
    render_page1_sidebar_filters,
    styled_axis,
)

# ─────────────────────────────────────────────

configure_page()
apply_global_style()

context = get_national_historical_context()
globals().update(context)

render_sidebar()

st.title(
    "Données nationales historiques et consolidées de la production d'électricité en France",
    text_alignment="center",
    width="stretch",
)


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
# Get raw national data from context (original dataframe before melting)
df_chart = context.get("df_nat_cons_agre_j")

# ─────────────────────────────────────────────
# CHART 1 — Historical Energy Production Time Series (Interactive)
# ─────────────────────────────────────────────
if df_chart is not None:
    # Prepare data for a day-of-month profile (1..31)
    df1 = df_chart.copy()

    if "date" in df1.columns:
        df1["plot_date"] = pd.to_datetime(df1["date"], errors="coerce")
    elif "mois" in df1.columns:
        df1["plot_date"] = pd.to_datetime(
            df1["mois"], utc=True, errors="coerce"
        ).dt.tz_convert(None)
    else:
        df1["plot_date"] = pd.NaT

    df1 = df1.dropna(subset=["plot_date"])
    df1["day"] = df1["plot_date"].dt.day

    source_columns = list(SOURCE_COLUMNS.values())
    y_variables = [column for column in source_columns if column in df1.columns]
    default_y = [
        column
        for column in ["nucleaire", "eolien", "hydraulique"]
        if column in y_variables
    ]

    # Add plot_date to df1 for sidebar filter function
    df1_with_dates = df1.copy()

    # Get filters from sidebar
    start_date, end_date, selected_y = render_page1_sidebar_filters(
        df1_with_dates, y_variables, default_y
    )

    apply_widget_text_style(color="#000000", font_size="0.95rem")

    # Validate dates and filter dataframe
    if start_date > end_date:
        st.error("La date de debut doit etre anterieure ou egale a la date de fin.")
        st.stop()

    df1 = df1[
        (df1["plot_date"].dt.date >= start_date)
        & (df1["plot_date"].dt.date <= end_date)
    ]

    # Create time series chart
    if selected_y:
        fig1 = go.Figure()

        for y_col in selected_y:
            df_plot = df1[["plot_date", y_col]].dropna().sort_values("plot_date")

            if not df_plot.empty:
                fig1.add_trace(
                    go.Scatter(
                        x=df_plot["plot_date"],
                        y=df_plot[y_col],
                        mode="lines",
                        name=y_col,
                        line={
                            "color": COLORS.get(y_col.capitalize(), "#3d3d3d"),
                            "width": 2.5,
                        },
                        hovertemplate=(
                            f"<b>{y_col}</b><br>"
                            "Date: %{x|%Y-%m-%d}<br>"
                            "Mois/Annee: %{x|%B %Y}<br>"
                            "Production: %{y:.2f}<extra></extra>"
                        ),
                    )
                )

        layout = {
            **BASE_LAYOUT,
            "title": {
                "text": "Production nationale d'electricite par jour du mois",
                "x": 0.5,
                "xanchor": "center",
                "y": 0.98,
                "yanchor": "top",
                "font": {"size": 30, "color": "#00dcff"},
            },
            "margin": {"l": 80, "r": 80, "t": 120, "b": 80},
            "xaxis": {
                **styled_axis("Jour du mois"),
                "title": {
                    "text": "Jour du mois",
                    "font": {"size": 16, "color": "#ffffff"},
                },
                "tickformat": "%d",
                "tickfont": {"size": 16, "color": "#ffffff"},
            },
            "yaxis": {
                **styled_axis("Production"),
                "title": {
                    "text": "Production",
                    "font": {"size": 16, "color": "#ffffff"},
                },
                "tickfont": {"size": 16, "color": "#ffffff"},
            },
            "legend": {
                "font": {"size": 16, "color": "#ffffff"},
                "bgcolor": "rgba(0,15,40,0.75)",
                "bordercolor": "rgba(0,180,255,0.3)",
                "borderwidth": 1,
            },
            "height": 500,
            "hovermode": "x unified",
        }
        fig1.update_layout(**layout)

        st.markdown(
            """
<div class="chart-card">
    <div class="chart-title">⚡ Production nationale par jour (profil journalier)</div>
  <div class="chart-desc">
      Axe X: jours. Axe Y: production.
      Choisissez une date de debut et de fin pour filtrer les donnees affichees.
        Selectionnez les filieres a comparer; une courbe est affichee par filiere.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig1, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.warning(
            "Veuillez sélectionner au moins une variable d'énergie pour afficher le graphique."
        )
else:
    st.error(
        "Les données ne sont pas disponibles. Veuillez vérifier le chargement des données."
    )

st.markdown(
    """
<div class="footer">
  ⚡ Project MiX-ENERGIE · Powered by FastAPI, Streamlit & Plotly · 2026
</div>
""",
    unsafe_allow_html=True,
)
