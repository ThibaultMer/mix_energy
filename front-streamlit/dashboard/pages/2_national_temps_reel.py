"""
Page 2: Vision national en temps reel des donnees de production d'electricite en France

"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from dashboard_share import (
    BASE_LAYOUT,
    COLORS,
    SOURCE_COLUMNS,
    apply_global_style,
    apply_widget_text_style,
    configure_page,
    get_national_realtime_context,
    get_realtime_numeric_columns,
    render_page2_sidebar_filters,
    render_sidebar,
    styled_axis,
)

configure_page()
apply_global_style()

context = get_national_realtime_context()
globals().update(context)
render_sidebar()

st.title(
    "Donnees nationales en temps reel de la production d'electricite en France",
    text_alignment="center",
    width="stretch",
)

# Get raw national realtime data from context (table2 = df_nat_tr_agre_j)
df_chart = context.get("df_nat_tr_agre_j")

if df_chart is not None:
    df2 = df_chart.copy()

    if "date" in df2.columns:
        df2["plot_date"] = pd.to_datetime(df2["date"], errors="coerce")
    elif all(column in df2.columns for column in ["annee", "mois", "jour"]):
        df2["plot_date"] = pd.to_datetime(
            {
                "year": pd.to_numeric(df2["annee"], errors="coerce"),
                "month": pd.to_numeric(df2["mois"], errors="coerce"),
                "day": pd.to_numeric(df2["jour"], errors="coerce"),
            },
            errors="coerce",
        )
    elif "mois" in df2.columns:
        df2["plot_date"] = pd.to_datetime(df2["mois"], errors="coerce")
    else:
        df2["plot_date"] = pd.NaT

    df2 = df2.dropna(subset=["plot_date"]).sort_values("plot_date")

    source_columns = [
        column for column in SOURCE_COLUMNS.values() if column in df2.columns
    ]
    y_variables = [
        column
        for column in source_columns
        if column in get_realtime_numeric_columns(df2)
    ]
    default_y = [
        column
        for column in ["nucleaire", "eolien", "hydraulique"]
        if column in y_variables
    ]
    if not default_y:
        default_y = y_variables[:3] if len(y_variables) >= 3 else y_variables

    apply_widget_text_style(color="#000000", font_size="0.95rem")
    selected_y = render_page2_sidebar_filters(y_variables, default_y)

    if selected_y:
        has_co2 = "taux_co2" in df2.columns and df2["taux_co2"].notna().any()

        if has_co2:
            fig2 = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.1,
                row_heights=[0.62, 0.38],
                subplot_titles=(
                    "Production nationale d'electricite",
                    "Taux de CO2 quotidien - derniere valeur du jour",
                ),
            )
        else:
            fig2 = go.Figure()

        for y_col in selected_y:
            df_plot = df2[["plot_date", y_col]].dropna().sort_values("plot_date")
            if df_plot.empty:
                continue

            trace = go.Scatter(
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

            if has_co2:
                fig2.add_trace(trace, row=1, col=1)
            else:
                fig2.add_trace(trace)

        if has_co2:
            df_co2 = df2[["plot_date", "taux_co2"]].dropna().copy()
            df_co2["day"] = df_co2["plot_date"].dt.floor("D")
            co2_daily = (
                df_co2.sort_values("plot_date")
                .groupby("day", as_index=False)
                .last()
                .sort_values("day")
            )

            fig2.add_trace(
                go.Bar(
                    x=co2_daily["day"],
                    y=co2_daily["taux_co2"],
                    marker_color="#00dcff",
                    hovertemplate=(
                        "Date: %{x|%Y-%m-%d}<br>Taux CO2: %{y:.2f}<extra></extra>"
                    ),
                    name="taux_co2",
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

        fig2.update_layout(
            paper_bgcolor=BASE_LAYOUT.get("paper_bgcolor"),
            plot_bgcolor=BASE_LAYOUT.get("plot_bgcolor"),
            font=BASE_LAYOUT.get("font"),
            title={
                "text": "Production nationale d'electricite et taux de CO2 - 30 derniers jours glissants",
                "x": 0.5,
                "xanchor": "center",
                "y": 0.98,
                "yanchor": "top",
                "font": {"size": 30, "color": "#ffffff"},
            },
            margin={"l": 80, "r": 80, "t": 120, "b": 80},
            legend={
                "font": {"size": 16, "color": "#ffffff"},
                "bgcolor": "rgba(0,15,40,0.75)",
                "bordercolor": "rgba(0,180,255,0.3)",
                "borderwidth": 1,
            },
            height=820 if has_co2 else 500,
            hovermode="x unified",
        )

        if has_co2:
            fig2.update_xaxes(
                **{
                    **styled_axis("Jour"),
                    "tickformat": "%d/%m",
                    "tickfont": {"size": 14, "color": "#ffffff"},
                },
                row=1,
                col=1,
            )
            fig2.update_xaxes(
                **{
                    **styled_axis("Jour"),
                    "title": {"text": "Jour", "font": {"size": 16, "color": "#ffffff"}},
                    "tickformat": "%d/%m",
                    "tickfont": {"size": 14, "color": "#ffffff"},
                },
                row=2,
                col=1,
            )
            fig2.update_yaxes(
                **{
                    **styled_axis("Production"),
                    "title": {
                        "text": "Production",
                        "font": {"size": 16, "color": "#ffffff"},
                    },
                    "tickfont": {"size": 14, "color": "#ffffff"},
                },
                row=1,
                col=1,
            )
            fig2.update_yaxes(
                **{
                    **styled_axis("Taux CO2 (g/kWh)"),
                    "title": {
                        "text": "Taux CO2 (g/kWh)",
                        "font": {"size": 16, "color": "#ffffff"},
                    },
                    "tickfont": {"size": 14, "color": "#ffffff"},
                },
                row=2,
                col=1,
            )
            fig2.update_annotations(font={"size": 18, "color": "#ffffff"})
        else:
            fig2.update_layout(
                xaxis={
                    **styled_axis("Jour"),
                    "title": {"text": "Jour", "font": {"size": 16, "color": "#ffffff"}},
                    "tickformat": "%d/%m",
                    "tickfont": {"size": 16, "color": "#ffffff"},
                },
                yaxis={
                    **styled_axis("Production"),
                    "title": {
                        "text": "Production",
                        "font": {"size": 16, "color": "#ffffff"},
                    },
                    "tickfont": {"size": 16, "color": "#ffffff"},
                },
            )

        st.markdown(
            """
<div class="chart-card">
    <div class="chart-title">⚡ Production nationale et 🟦 CO2 quotidien (30 jours glissants)</div>
  <div class="chart-desc">
        Les deux graphiques sont affiches l'un au dessus de l'autre avec la meme largeur,
        afin de faciliter la comparaison entre la production d'electricite et le taux de CO2.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig2, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.warning(
            "Veuillez selectionner au moins une variable d'energie pour afficher le graphique."
        )
else:
    st.error(
        "Les donnees ne sont pas disponibles. Veuillez verifier le chargement des donnees."
    )

st.markdown(
    """
<div class="footer">
  ⚡ Project MiX-ENERGIE · Powered by FastAPI, Streamlit & Plotly · 2026
</div>
""",
    unsafe_allow_html=True,
)
