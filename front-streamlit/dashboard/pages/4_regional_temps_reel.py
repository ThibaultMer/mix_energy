"""
Page 4: Vision régionale en temps réel des données de production d'électricité en France

"""

# Import necessary libraries
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import importlib

try:
    _autorefresh_module = importlib.import_module("streamlit_autorefresh")
    st_autorefresh = getattr(_autorefresh_module, "st_autorefresh", None)
except ImportError:  # pragma: no cover - optional dependency
    st_autorefresh = None

from dashboard_share import (
    BASE_LAYOUT,
    apply_global_style,
    apply_widget_text_style,
    clear_realtime_cache,
    configure_page,
    get_energy_types,
    get_region_options,
    get_realtime_numeric_columns,
    get_regional_realtime_context,
    render_sidebar,
    styled_axis,
)

# ─────────────────────────────────────────────

configure_page()
apply_global_style()

REGIONS = get_region_options()
ENERGY_TYPES = get_energy_types()

render_sidebar()

default_region = "Île-de-France" if "Île-de-France" in REGIONS else REGIONS[0]
selected_region = st.selectbox(
    "Région analysée:",
    options=REGIONS,
    index=REGIONS.index(default_region),
    key="regional_rt_region_choice",
)

with st.sidebar:
    st.markdown(
        '<div class="sidebar-section">🔄 Rafraichissement</div>', unsafe_allow_html=True
    )
    if st.button("Actualiser les donnees", key="refresh_reg_rt"):
        clear_realtime_cache()
        st.rerun()

    auto_refresh_enabled = st.toggle(
        "Auto-refresh", value=True, key="toggle_reg_rt_auto"
    )
    auto_refresh_minutes = st.selectbox(
        "Intervalle (minutes)",
        options=[1, 5, 15],
        index=1,
        key="interval_reg_rt_auto",
    )

if auto_refresh_enabled and st_autorefresh:
    st_autorefresh(interval=auto_refresh_minutes * 60 * 1000, key="autorefresh_reg_rt")

context = get_regional_realtime_context(selected_region)
globals().update(context)

st.title(
    "Données régionales en temps réel de la production d'électricité en France",
    text_alignment="center",
    width="stretch",
)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df_chart = context.get("df_reg_tr_agre_j")


# ─────────────────────────────────────────────
# CHART 4 — Regional Realtime Time Series (Interactive)
# ─────────────────────────────────────────────
if df_chart is not None:
    df4 = df_chart.copy()

    if "mois" in df4.columns:
        df4["mois"] = pd.to_datetime(df4["mois"], utc=True).dt.tz_convert(None)
        df4["year"] = df4["mois"].dt.year
        df4["month"] = df4["mois"].dt.month
        df4["day"] = df4["mois"].dt.day

    region_col = "libelle_region" if "libelle_region" in df4.columns else "region"
    if region_col not in df4.columns:
        st.error("Aucune colonne de région trouvée (libelle_region ou region).")
        st.stop()

    y_variables = get_realtime_numeric_columns(
        df4, extra_excluded={"code_insee_region", region_col}
    )
    x_variables = ["year", "month", "day"]

    apply_widget_text_style(color="#c8e6ff")

    col1, col2 = st.columns(2)
    with col1:
        selected_x = st.selectbox(
            "Dimension du Temps (X-axis):",
            x_variables,
            index=x_variables.index("month"),
            key="regional_rt_x_select",
        )
    with col2:
        selected_y = st.multiselect(
            "Sources d'Energies (Y-axis):",
            y_variables,
            default=y_variables[:3] if len(y_variables) >= 3 else y_variables,
            key="regional_rt_y_select",
        )
    df4 = df4[df4[region_col].astype(str) == selected_region]

    if selected_y:
        fig4 = go.Figure()
        for y_col in selected_y:
            df_plot = df4[[selected_x, y_col]].dropna().sort_values(selected_x)
            if not df_plot.empty:
                fig4.add_trace(
                    go.Scatter(
                        x=df_plot[selected_x],
                        y=df_plot[y_col],
                        mode="lines+markers",
                        name=y_col,
                        hovertemplate=(
                            f"<b>{y_col}</b><br>"
                            f"{selected_x}: %{{x}}<br>"
                            f"Valeur: %{{y:.2f}}<extra></extra>"
                        ),
                    )
                )

        fig4.update_layout(
            **BASE_LAYOUT,
            title={
                "text": "Production régionale d'électricité - Données Temps Réel",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": "#00dcff"},
            },
            xaxis=styled_axis(f"Time Dimension ({selected_x.capitalize()})"),
            yaxis=styled_axis("Production Value"),
            height=500,
            hovermode="x unified",
        )

        st.markdown(
            """
<div class="chart-card">
  <div class="chart-title">📈 Série Temporelle Régionale (Temps Réel)</div>
  <div class="chart-desc">
    Explorez l'évolution des variables de production par région en sélectionnant une dimension temporelle,
    une ou plusieurs variables Y, puis une région spécifique.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig4, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.warning(
            "Veuillez sélectionner au moins une variable pour afficher le graphique."
        )
else:
    st.error(
        "Les données ne sont pas disponibles. Veuillez vérifier le chargement des données."
    )


st.markdown("---")
st.subheader("Comparaison régionale et nationale")

st.markdown(
    """
<div class="chart-card">
  <div class="chart-title">Lorem ipsum</div>
  <div class="chart-desc">
    Lorem ipsum dolor sit amet, consectetur adipiscing elit,
    sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
    nisi ut aliquip ex ea commodo consequat.
    Duis aute irure dolor in reprehenderit in voluptate
    velit esse cillum dolore eu fugiat nulla pariatur.
    Excepteur sint occaecat cupidatat non proident,
    sunt in culpa qui officia deserunt mollit anim id est laborum."
  </div>
</div>
""",
    unsafe_allow_html=True,
)
