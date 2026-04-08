"""
Page 3: Vision régionale historique et consolidée des données de production d'électricité en France

"""

# Import necessary libraries
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from dashboard_share import (
    BASE_LAYOUT,
    SOURCE_COLUMNS,
    apply_global_style,
    configure_page,
    get_energy_types,
    get_regional_historical_context,
    get_region_options,
    render_sidebar,
)

FONT_COLOR = "#c8e6ff"
AXIS_COLOR = "rgba(0,180,255,0.25)"

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
    key="regional_hist_region_select",
)

context = get_regional_historical_context(selected_region)
globals().update(context)

st.title(
    "Données régionales historiques et consolidées de la production d'électricité en France",
    text_alignment="center",
    width="stretch",
)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
df_reg_cons_agre_j = context.get("df_reg_cons_agre_j")


# ─────────────────────────────────────────────
# CHART 3 — Heatmap: Region × Energy Type
# ─────────────────────────────────────────────
if df_reg_cons_agre_j is None:
    st.error("Les données régionales historiques (table3) ne sont pas disponibles.")
    st.stop()

region_col = (
    "libelle_region" if "libelle_region" in df_reg_cons_agre_j.columns else "region"
)

source_columns = SOURCE_COLUMNS

value_columns = [
    column for column in source_columns.values() if column in df_reg_cons_agre_j.columns
]

df3 = df_reg_cons_agre_j.melt(
    id_vars=[region_col],
    value_vars=value_columns,
    var_name="source_column",
    value_name="Production_TWh",
)
inverse_sources = {column: label for label, column in source_columns.items()}
df3["EnergyType"] = df3["source_column"].map(inverse_sources)
df3["Region"] = df3[region_col].astype(str)
selected_regions = [selected_region]
selected_types = ENERGY_TYPES
df3 = df3[df3.EnergyType.isin(selected_types) & df3.Region.isin(selected_regions)]
pivot = df3.pivot_table(
    index="Region", columns="EnergyType", values="Production_TWh", aggfunc="sum"
).fillna(0)

fig3 = go.Figure(
    data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "rgba(0,10,40,1)"],
            [0.25, "rgba(0,60,140,1)"],
            [0.5, "rgba(0,160,220,1)"],
            [0.75, "rgba(0,230,255,1)"],
            [1.0, "rgba(180,255,255,1)"],
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="TWh", font=dict(color=FONT_COLOR, size=11)),
            tickfont=dict(color=FONT_COLOR, size=10),
            bgcolor="rgba(0,10,30,0.5)",
            outlinecolor="rgba(0,180,255,0.2)",
        ),
        hovertemplate="Region: <b>%{y}</b><br>Source: <b>%{x}</b><br>Production: <b>%{z:.2f} TWh</b><extra></extra>",
        text=np.asarray(pivot.values, dtype=float).round(1),
        texttemplate="%{text}",
        textfont=dict(size=9, color="rgba(255,255,255,0.7)"),
    )
)
fig3.update_layout(
    **BASE_LAYOUT,
    xaxis=dict(tickfont=dict(size=20, color=FONT_COLOR), linecolor=AXIS_COLOR),
    yaxis=dict(tickfont=dict(size=19, color=FONT_COLOR), linecolor=AXIS_COLOR),
    height=420,
)

st.markdown(
    """
<div class="chart-card">
  <div class="chart-title">🗺️ Regional Energy Mix Heatmap</div>
  <div class="chart-desc">
    Heatmap of electricity production (TWh) across all 12 French metropolitan regions and 6 energy source categories.
    Brighter cells = higher output. Useful for identifying regional specializations and energy dependence patterns.
  </div>
</div>
""",
    unsafe_allow_html=True,
)
st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})


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
