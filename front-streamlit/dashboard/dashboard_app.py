"""
MIX-ENERGIE PROJECT
Homepage for the multipage Streamlit dashboard.
"""

import streamlit as st

from dashboard_share import (
    apply_global_style,
    configure_page,
)

configure_page()
apply_global_style()

st.markdown(
    """
<div class="hero-header">
    <span class="hero-icon">⚡</span>
    <p class="hero-title">PRODUCTION ELECTRIQUE FRANCAISE</p>
    <p class="hero-subtitle">Réseau national · Réseaux régionaux · Émissions de CO2 · Données consolidées</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
/* Pixel-perfect home navigation for st.page_link */
div[data-testid="stPageLink"] {
    margin: 0.08rem 0 0.18rem 0;
}

div[data-testid="stPageLink"] > a,
div[data-testid="stPageLink"] a {
    display: flex !important;
    justify-content: center;
    align-items: center;
    width: 100% !important;
    min-height: 6rem;
    padding: 1.2rem 1rem;
    border-radius: 12px;
    border: 1px solid rgba(0, 180, 255, 0.26);
    background: linear-gradient(180deg, rgba(9, 32, 70, 0.9) 0%, rgba(4, 19, 50, 0.88) 100%);
    color: #7dd6ff !important;
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.35rem !important;
    font-weight: 700;
    letter-spacing: 0.035em;
    line-height: 1.15;
    text-decoration: none !important;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0, 130, 220, 0.18);
    transition: transform 0.15s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

div[data-testid="stPageLink"] > a *,
div[data-testid="stPageLink"] a * {
    color: inherit !important;
    font-size: 1.35rem !important;
    line-height: 1.2 !important;
    font-weight: 700 !important;
    text-decoration: none !important;
}

div[data-testid="stPageLink"] > a:hover,
div[data-testid="stPageLink"] a:hover {
    border-color: rgba(0, 220, 255, 0.62);
    background: linear-gradient(180deg, rgba(11, 38, 84, 0.94) 0%, rgba(5, 23, 58, 0.92) 100%);
    box-shadow: 0 10px 28px rgba(0, 170, 255, 0.28);
    transform: translateY(-1px);
}

div[data-testid="stPageLink"] > a:focus-visible,
div[data-testid="stPageLink"] a:focus-visible {
    outline: 2px solid rgba(120, 232, 255, 0.9);
    outline-offset: 2px;
}

div[data-testid="stPageLink"] > a[aria-current="page"],
div[data-testid="stPageLink"] a[aria-current="page"] {
    border-color: rgba(0, 220, 255, 0.78);
    background: linear-gradient(180deg, rgba(8, 50, 104, 0.96) 0%, rgba(6, 30, 72, 0.94) 100%);
    box-shadow: 0 0 0 1px rgba(0, 220, 255, 0.26), 0 10px 30px rgba(0, 170, 255, 0.3);
}
</style>
""",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.page_link(
        "pages/1_national_historique.py",
        label="National Historique",
        use_container_width=True,
    )
with col2:
    st.page_link(
        "pages/2_national_temps_reel.py",
        label="National Temps Reel",
        use_container_width=True,
    )
with col3:
    st.page_link(
        "pages/3_regional_historique.py",
        label="Regional Historique",
        use_container_width=True,
    )
with col4:
    st.page_link(
        "pages/4_regional_temps_reel.py",
        label="Regional Temps Reel",
        use_container_width=True,
    )

st.markdown(
    """
<div class="chart-card">
  <div class="chart-title">Accueil</div>
  <div class="chart-desc">
    Cette page d'accueil est volontairement legere: elle ne charge aucune donnee.
    Chaque page fonctionnelle charge uniquement ses propres informations depuis FastAPI au moment ou vous l'ouvrez.
    Cela permet un demarrage rapide de l'accueil et un usage plus cible des appels API.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="chart-card">
  <div class="chart-title">Pages disponibles</div>
  <div class="chart-desc">
    1. National Historique: donnees annee en cours + annee precedente.<br>
    2. National Temps Reel: donnees du mois en cours avec refresh.<br>
    3. Regional Historique: region choisie, annee en cours + annee precedente.<br>
    4. Regional Temps Reel: region choisie, mois en cours avec refresh.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="chart-card">
  <div class="chart-title">Remerciements</div>
  <div class="chart-desc">
    Nous remercions nos camarades de formation ainsi que nos deux formateurs et les autres intervenants pour leur soutien et leurs conseils tout au long de ce projet. Un grand merci à Google Cloud pour l'accès presque gratuit à la plateforme et aux données. Merci ainsi qu'à la communauté open source pour les données et les outils utilisés.
  </div>
</div>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<div class="footer">
  ⚡ Project MiX-ENERGIE · Powered by FastAPI, Streamlit & Plotly · 2026
</div>
""",
    unsafe_allow_html=True,
)
