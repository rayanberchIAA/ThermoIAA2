"""
==============================================================================
app.py — Interface Streamlit : ThermoIAA
Application : Refroidissement & Congélation en industrie agroalimentaire
==============================================================================
Lancement : streamlit run app.py
==============================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import copy

# ── Modules locaux ────────────────────────────────────────────────────────────
from calculations import (
    ParamsRefroidissement,
    ParamsCongélation,
    bilan_refroidissement,
    bilan_congelation,
    sensibilite_COP,
    sensibilite_T_finale,
    sensibilite_masse,
    sensibilite_prix_elec,
    sensibilite_duree,
    profil_temperature,
    comparer_scenarios,
)
from utils import (
    interpreter_resultats,
    recommander_scenario,
    exporter_excel,
    exporter_pdf,
    generer_rapport_markdown,
    fmt,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ThermoIAA — Refroidissement & Congélation",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Configuration PWA ────────────────────────────────────────────────────────
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#0d2b45">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

st.markdown("""
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
        .then(registration => console.log('SW registered'))
        .catch(error => console.log('SW registration failed'));
}
</script>
""", unsafe_allow_html=True)

# ── CSS personnalisé — MAIN CONTENT ONLY (Sidebar styling removed to prevent conflicts) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ══════════════════════════════════════════════
   ROOT — Palette industrielle froide
   ══════════════════════════════════════════════ */
:root {
    --bg         : #f0f2f5;
    --surface    : #ffffff;
    --surface-2  : #f7f8fa;
    --navy       : #0b1e2d;
    --navy-mid   : #122840;
    --cyan       : #00b4d8;
    --cyan-dim   : #0096b4;
    --green      : #00c48c;
    --amber      : #f59e0b;
    --red        : #ef4444;
    --border     : #e0e4eb;
    --border-dark: #c8cfd9;
    --text       : #1a2535;
    --text-mid   : #4a5568;
    --text-muted : #8494a7;
    --mono       : 'DM Mono', 'Courier New', monospace;
    --sans       : 'DM Sans', system-ui, sans-serif;
    --display    : 'Syne', sans-serif;
}

/* ══════════════════════════════════════════════
   GLOBAL
   ══════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: var(--sans);
    background-color: var(--bg);
    color: var(--text);
}

/* Streamlit main block padding reduction */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}

/* ══════════════════════════════════════════════
   HEADER — dark plate, cyan rule, Syne display
   ══════════════════════════════════════════════ */
.main-header {
    background: var(--navy);
    padding: 1.8rem 2.2rem 1.6rem;
    border-radius: 2px;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--cyan) 0%, var(--green) 100%);
}
.main-header::after {
    content: 'THERMO IAA';
    position: absolute;
    right: 2.2rem;
    top: 50%;
    transform: translateY(-50%);
    font-family: var(--display);
    font-size: 5rem;
    font-weight: 800;
    color: rgba(255,255,255,0.04);
    letter-spacing: -0.02em;
    pointer-events: none;
    user-select: none;
    white-space: nowrap;
}
.main-header h1 {
    font-family: var(--display);
    font-size: 1.45rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 .45rem 0;
    letter-spacing: -0.01em;
    line-height: 1;
}
.main-header p {
    font-family: var(--mono);
    font-size: .78rem;
    margin: 0;
    color: #5d8aaa;
    line-height: 1.7;
    letter-spacing: 0.03em;
}

/* ══════════════════════════════════════════════
   KPI CARDS — monospace values, sharp geometry
   ══════════════════════════════════════════════ */
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 1rem 1.15rem .9rem;
    margin-bottom: .7rem;
    position: relative;
    transition: box-shadow .15s ease;
}
.kpi-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--cyan);
    border-radius: 2px 0 0 2px;
}
.kpi-card:hover {
    box-shadow: 0 4px 18px rgba(0,0,0,.07);
}
.kpi-label {
    font-family: var(--mono);
    font-size: .68rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .09em;
    margin-bottom: .3rem;
}
.kpi-value {
    font-family: var(--mono);
    font-size: 1.7rem;
    font-weight: 500;
    color: var(--navy);
    line-height: 1.1;
    letter-spacing: -0.02em;
}
.kpi-unit {
    font-family: var(--mono);
    font-size: .72rem;
    color: var(--text-muted);
    margin-top: .15rem;
    letter-spacing: .04em;
}

/* Variants */
.kpi-card-accent::before { background: var(--green); }
.kpi-card-accent .kpi-value { color: #027a5c; }
.kpi-card-warn::before   { background: var(--amber); }
.kpi-card-warn .kpi-value   { color: #92580a; }

/* ══════════════════════════════════════════════
   SECTION BADGE
   ══════════════════════════════════════════════ */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    background: var(--navy);
    color: var(--cyan);
    border-radius: 2px;
    padding: .18rem .75rem;
    font-family: var(--mono);
    font-size: .72rem;
    font-weight: 500;
    margin-bottom: .7rem;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.section-badge::before {
    content: '//';
    opacity: .5;
}

/* ══════════════════════════════════════════════
   EQUATION BOX
   ══════════════════════════════════════════════ */
.eq-box {
    background: var(--navy);
    border-radius: 2px;
    padding: .8rem 1.2rem;
    font-family: var(--mono);
    font-size: .87rem;
    color: #7ec8e3;
    margin: .45rem 0;
    border-left: 3px solid var(--cyan);
}

/* ══════════════════════════════════════════════
   INTERPRETATION BOX
   ══════════════════════════════════════════════ */
.interp-box {
    background: #f2fbf8;
    border-left: 3px solid var(--green);
    border-radius: 0 2px 2px 0;
    padding: .75rem 1.1rem;
    margin: .4rem 0;
    font-size: .91rem;
    color: var(--text);
    line-height: 1.6;
}

/* ══════════════════════════════════════════════
   SIDEBAR — structured, dark-navy header strip
   ══════════════════════════════════════════════ */
.stSidebar {
    background-color: var(--surface-2) !important;
    border-right: 1px solid var(--border) !important;
}

.stSidebar [data-testid="stMarkdownContainer"] h2 {
    font-family: var(--display);
    color: var(--navy);
    font-size: .9rem;
    font-weight: 800;
    margin-top: 1.2rem;
    margin-bottom: .55rem;
    padding-bottom: .35rem;
    border-bottom: 2px solid var(--cyan);
    letter-spacing: .01em;
    text-transform: uppercase;
}

.stSidebar [data-testid="stMarkdownContainer"] h3 {
    font-family: var(--mono);
    color: var(--text-muted);
    font-size: .72rem;
    font-weight: 500;
    margin-top: 1rem;
    margin-bottom: .3rem;
    text-transform: uppercase;
    letter-spacing: .1em;
}

/* ══════════════════════════════════════════════
   STREAMLIT TAB STRIP — sharpen the tab look
   ══════════════════════════════════════════════ */
div[data-testid="stTabs"] > div:first-child {
    border-bottom: 2px solid var(--border-dark) !important;
    gap: 0 !important;
}
button[data-baseweb="tab"] {
    font-family: var(--mono) !important;
    font-size: .75rem !important;
    letter-spacing: .06em !important;
    text-transform: uppercase !important;
    padding: .5rem 1.1rem !important;
    border-radius: 0 !important;
    color: var(--text-muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--navy) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--cyan) !important;
}

/* ══════════════════════════════════════════════
   STREAMLIT METRICS (fallback if used)
   ══════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: .8rem 1rem;
}

/* ══════════════════════════════════════════════
   BUTTONS
   ══════════════════════════════════════════════ */
.stButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"] {
    background: var(--navy) !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 2px !important;
    font-family: var(--mono) !important;
    font-size: .78rem !important;
    letter-spacing: .07em !important;
    text-transform: uppercase !important;
    transition: background .15s, color .15s !important;
}
.stButton > button[kind="primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
    background: var(--cyan) !important;
    color: var(--navy) !important;
}

/* ══════════════════════════════════════════════
   DATAFRAMES
   ══════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 2px;
}

/* ══════════════════════════════════════════════
   DIVIDER
   ══════════════════════════════════════════════ */
hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}

/* ══════════════════════════════════════════════
   DARK MODE OVERRIDES
   ══════════════════════════════════════════════ */
.streamlit-dark-mode .stSidebar,
.streamlit-dark-mode section[data-testid="stSidebar"] {
    background-color: #0a1520 !important;
    border-right-color: #1d2f40 !important;
}
.streamlit-dark-mode .stSidebar [data-testid="stMarkdownContainer"] h2 {
    color: #e2edf5 !important;
}
.streamlit-dark-mode .stSidebar [data-testid="stMarkdownContainer"] h3 {
    color: #4a7a9b !important;
}
.streamlit-dark-mode .kpi-card {
    background: #0f1e2e;
    border-color: #1d2f40;
}
.streamlit-dark-mode .kpi-value { color: #d6eaf8; }
.streamlit-dark-mode .kpi-label { color: #4a6a82; }
.streamlit-dark-mode .kpi-unit  { color: #4a6a82; }
.streamlit-dark-mode .interp-box { background: #0d2218; border-left-color: var(--green); color: #c5e8d8; }
.streamlit-dark-mode .section-badge { background: #0d1e2d; color: var(--cyan); }
.streamlit-dark-mode .eq-box { background: #060f18; color: #5cbddb; border-left-color: var(--cyan); }

html[data-theme="dark"] .stSidebar { background-color: #0a1520; }
html[data-theme="dark"] .stSidebar [data-testid="stMarkdownContainer"] h2,
html[data-theme="dark"] .stSidebar [data-testid="stMarkdownContainer"] h3 {
    color: #d6eaf8;
}
.streamlit-dark-mode .stSidebar button,
.streamlit-dark-mode .stSidebar .stButton > button {
    background-color: #0f1e2e !important;
    color: var(--cyan) !important;
    border-color: var(--cyan) !important;
}
</style>
""", unsafe_allow_html=True)

components.html("""
<script>
(function() {
  const parentDoc = window.parent.document;
  const root = parentDoc.documentElement;

  function updateDarkModeClass() {
    const container = parentDoc.querySelector('div[data-testid="stAppViewContainer"]');
    if (!container) {
      return;
    }
    const style = window.parent.getComputedStyle(container);
    const rgb = style.color.match(/(\d+),\s*(\d+),\s*(\d+)/);
    if (rgb) {
      const r = Number(rgb[1]);
      const g = Number(rgb[2]);
      const b = Number(rgb[3]);
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      root.classList.toggle('streamlit-dark-mode', brightness > 128);
    }
  }

  updateDarkModeClass();
  window.setInterval(updateDarkModeClass, 500);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', updateDarkModeClass);
})();
</script>
""", height=1, scrolling=False)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
  <h1>ThermoIAA — Refroidissement &amp; Congélation</h1>
  <p>Dimensionnement thermodynamique &nbsp;·&nbsp; Industrie Agroalimentaire &nbsp;·&nbsp; v1.0<br>
  Rayane Berch — 1CI IAA &nbsp;·&nbsp; Professeure Amal Ibijbijen</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR INPUT COLLECTION — Modular & Maintainable
# ─────────────────────────────────────────────────────────────────────────────

def collect_sidebar_inputs():
    """
    Collect all sidebar inputs in a single function.
    Returns a dictionary with all input values and metadata.
    
    ADVANTAGES:
    - All sidebar logic in one place (easier to maintain)
    - Clean separation between input collection and computation
    - Easy to debug or refactor sidebar inputs
    - Reusable across multiple Streamlit reruns
    """
    
    sidebar_data = {}
    
    with st.sidebar:
        # ── HEADER ────────────────────────────────────────────────────────────
        st.markdown("## Données d'entrée")
        st.write("Définir tous les paramètres du procédé de refroidissement ou congélation.")
        
        # ── MODE DE TRAITEMENT ────────────────────────────────────────────────
        st.markdown("### Mode de traitement")
        mode = st.radio(
            "Sélectionner le procédé :",
            ["Refroidissement simple", "Congélation complète"],
            help="Refroidissement : sans changement d'état. Congélation : passage à T négative.",
            key="mode_select"
        )
        sidebar_data["is_congelation"] = "Congélation" in mode
        sidebar_data["mode_name"] = mode
        
        st.divider()
        
        # ── PRODUIT ALIMENTAIRE ───────────────────────────────────────────────
        st.markdown("### Produit alimentaire")
        
        produits_predefinis = {
            "Poulet (volaille)"    : {"cp": 3.31, "cp_c": 1.68, "L": 246, "T_cong": -1.5, "w": 0.74},
            "Bœuf (viande rouge)"  : {"cp": 3.52, "cp_c": 1.75, "L": 251, "T_cong": -1.7, "w": 0.75},
            "Poisson (saumon)"     : {"cp": 3.60, "cp_c": 1.80, "L": 257, "T_cong": -2.0, "w": 0.76},
            "Fromage (pâte dure)"  : {"cp": 2.55, "cp_c": 1.35, "L": 180, "T_cong": -3.5, "w": 0.38},
            "Jus de fruit"         : {"cp": 3.90, "cp_c": 2.00, "L": 292, "T_cong": -1.0, "w": 0.88},
            "Légumes (haricots)"   : {"cp": 3.85, "cp_c": 1.95, "L": 285, "T_cong": -1.2, "w": 0.87},
            "Personnalisé"         : None,
        }
        
        produit_choix = st.selectbox(
            "Produit :",
            list(produits_predefinis.keys()),
            help="Valeurs typiques issues de la littérature IAA.",
            key="produit_select"
        )
        preset = produits_predefinis[produit_choix]
        sidebar_data["produit_choix"] = produit_choix
        sidebar_data["preset"] = preset
        
        st.divider()
        
        # ── PARAMÈTRES DU LOT ─────────────────────────────────────────────────
        st.markdown("### Paramètres du lot")
        
        masse = st.number_input(
            "Masse du produit (kg)",
            min_value=10.0, max_value=50_000.0, value=500.0, step=50.0,
            help="Masse totale de produit à traiter par opération.",
            key="masse_input"
        )
        sidebar_data["masse"] = masse
        
        st.divider()
        
        # ── TEMPÉRATURES ─────────────────────────────────────────────────────
        st.markdown("### Températures")
        
        T_ini = st.number_input(
            "Température initiale (°C)",
            min_value=-5.0, max_value=100.0, value=20.0, step=0.5,
            help="Température du produit avant traitement (ex. : sortie de fabrication).",
            key="T_ini_input"
        )
        sidebar_data["T_ini"] = T_ini
        
        if sidebar_data["is_congelation"]:
            T_cong_default = preset["T_cong"] if preset else -1.5
            T_cong = st.number_input(
                "Température de congélation (°C)",
                min_value=-10.0, max_value=0.0, value=T_cong_default, step=0.1,
                help="Point de début de solidification du produit (cryoscopique).",
                key="T_cong_input"
            )
            sidebar_data["T_cong"] = T_cong
            
            T_fin = st.number_input(
                "Température finale souhaitée (°C)",
                min_value=-40.0, max_value=-1.0, value=-18.0, step=1.0,
                help="Température de conservation (norme : -18°C pour congélation).",
                key="T_fin_cong_input"
            )
            sidebar_data["T_fin"] = T_fin
        else:
            sidebar_data["T_cong"] = -1.5  # non utilisé
            T_fin = st.number_input(
                "Température finale souhaitée (°C)",
                min_value=-5.0, max_value=30.0, value=4.0, step=0.5,
                help="Température cible après refroidissement (ex. : 4°C réfrigération).",
                key="T_fin_refroid_input"
            )
            sidebar_data["T_fin"] = T_fin
        
        st.divider()
        
        # ── PROPRIÉTÉS THERMIQUES ────────────────────────────────────────────
        st.markdown("### Propriétés thermiques")
        
        cp_default = preset["cp"] if preset else 3.50
        cp = st.number_input(
            "Cp produit frais (kJ/kg·K)",
            min_value=0.5, max_value=4.2, value=cp_default, step=0.01,
            help="Chaleur massique avant congélation.",
            key="cp_input"
        )
        sidebar_data["cp"] = cp
        
        if sidebar_data["is_congelation"]:
            cp_c_default = preset["cp_c"] if preset else 1.75
            cp_congele = st.number_input(
                "Cp produit congelé (kJ/kg·K)",
                min_value=0.5, max_value=2.5, value=cp_c_default, step=0.01,
                help="Chaleur massique du produit congelé (≈ moitié du Cp frais).",
                key="cp_congele_input"
            )
            sidebar_data["cp_congele"] = cp_congele
            
            L_default = preset["L"] if preset else 250.0
            L_cong = st.number_input(
                "Chaleur latente de congélation (kJ/kg)",
                min_value=50.0, max_value=334.0, value=float(L_default), step=1.0,
                help="Chaleur latente de solidification de l'eau dans le produit.",
                key="L_cong_input"
            )
            sidebar_data["L_cong"] = L_cong
            
            w_default = preset["w"] if preset else 0.75
            fraction_eau = st.number_input(
                "Fraction d'eau congelable (-)",
                min_value=0.10, max_value=0.99, value=w_default, step=0.01,
                help="Fraction massique d'eau congelable dans le produit.",
                key="fraction_eau_input"
            )
            sidebar_data["fraction_eau"] = fraction_eau
        else:
            sidebar_data["cp_congele"] = 1.75
            sidebar_data["L_cong"] = 250.0
            sidebar_data["fraction_eau"] = 0.75
        
        st.divider()
        
        # ── DURÉE & MACHINE FRIGORIFIQUE ──────────────────────────────────────
        st.markdown("### Durée & Machine")
        
        duree = st.number_input(
            "Durée de traitement (h)",
            min_value=0.5, max_value=48.0, value=8.0, step=0.5,
            help="Durée souhaitée pour l'opération de refroidissement/congélation.",
            key="duree_input"
        )
        sidebar_data["duree"] = duree
        
        COP = st.number_input(
            "COP de la machine frigorifique (-)",
            min_value=0.5, max_value=8.0, value=3.0, step=0.1,
            help="Coefficient de performance. Plus le COP est élevé, plus la machine est efficace.",
            key="COP_input"
        )
        sidebar_data["COP"] = COP
        
        if sidebar_data["is_congelation"]:
            P_dispo = st.number_input(
                "Puissance frigorifique disponible (kW) — optionnel",
                min_value=0.0, max_value=5000.0, value=0.0, step=5.0,
                help="Si renseigné, calcule le temps minimal de traitement avec cette puissance.",
                key="P_dispo_input"
            )
            sidebar_data["P_dispo"] = P_dispo if P_dispo > 0 else None
        else:
            sidebar_data["P_dispo"] = None
        
        st.divider()
        
        # ── DONNÉES ÉCONOMIQUES ──────────────────────────────────────────────
        st.markdown("### Données économiques")
        
        prix_elec = st.number_input(
            "Prix de l'électricité (MAD/kWh)",
            min_value=0.01, max_value=20.0, value=1.4, step=0.1,
            help="Tarif industriel moyen au Maroc : généralement ≥ 1 MAD/kWh pour applications agroalimentaires.",
            key="prix_elec_input"
        )
        if prix_elec < 1.0:
            st.warning(
                "Attention : Ce prix est inférieur au tarif industriel typique au Maroc (≥ 1 MAD/kWh). Vérifiez la valeur saisie."
            )
        sidebar_data["prix_elec"] = prix_elec

        
        nb_ops = st.number_input(
            "Nombre d'opérations / jour",
            min_value=1, max_value=24, value=2, step=1,
            help="Nombre de lots traités par jour.",
            key="nb_ops_input"
        )
        sidebar_data["nb_ops"] = int(nb_ops)
        
        nb_jours = st.number_input(
            "Jours de fonctionnement / an",
            min_value=1, max_value=365, value=300, step=5,
            help="Nombre de jours d'exploitation annuel.",
            key="nb_jours_input"
        )
        sidebar_data["nb_jours"] = int(nb_jours)
        
        st.divider()
        
        # ── BUTTON: LANCER LES CALCULS ───────────────────────────────────────
        calc_btn = st.button(
            "Lancer les calculs",
            type="primary",
            use_container_width=True,
            help="Cliquer pour exécuter les calculs avec les paramètres saisis.",
            key="calc_button"
        )
        sidebar_data["calc_btn"] = calc_btn
    
    return sidebar_data


# ─────────────────────────────────────────────────────────────────────────────
# COLLECT SIDEBAR INPUTS
# ─────────────────────────────────────────────────────────────────────────────

sidebar_inputs = collect_sidebar_inputs()

# Extract values from sidebar dictionary for clarity
is_congelation = sidebar_inputs["is_congelation"]
mode = sidebar_inputs["mode_name"]
produit_choix = sidebar_inputs["produit_choix"]
masse = sidebar_inputs["masse"]
T_ini = sidebar_inputs["T_ini"]
T_cong = sidebar_inputs["T_cong"]
T_fin = sidebar_inputs["T_fin"]
cp = sidebar_inputs["cp"]
cp_congele = sidebar_inputs["cp_congele"]
L_cong = sidebar_inputs["L_cong"]
fraction_eau = sidebar_inputs["fraction_eau"]
duree = sidebar_inputs["duree"]
COP = sidebar_inputs["COP"]
P_dispo = sidebar_inputs["P_dispo"]
prix_elec = sidebar_inputs["prix_elec"]
nb_ops = sidebar_inputs["nb_ops"]
nb_jours = sidebar_inputs["nb_jours"]
calc_btn = sidebar_inputs["calc_btn"]


# ─────────────────────────────────────────────────────────────────────────────
# CALCULS PRINCIPAUX
# ─────────────────────────────────────────────────────────────────────────────

# On stocke en session_state pour persistance entre reruns
if "resultats" not in st.session_state:
    st.session_state["resultats"] = None
    st.session_state["historique"] = []

if calc_btn:
    if is_congelation:
        params = ParamsCongélation(
            masse=masse, T_initiale=T_ini, T_finale=T_fin,
            cp_produit=cp, duree=duree, COP=COP,
            prix_elec=prix_elec, nb_operations=int(nb_ops), nb_jours=int(nb_jours),
            T_congelation=T_cong, cp_congele=cp_congele,
            L_congelation=L_cong, fraction_eau=fraction_eau,
            P_frigo_dispo=P_dispo,
        )
        r = bilan_congelation(params)
        mode_calc = "congelation"
    else:
        params = ParamsRefroidissement(
            masse=masse, T_initiale=T_ini, T_finale=T_fin,
            cp_produit=cp, duree=duree, COP=COP,
            prix_elec=prix_elec, nb_operations=int(nb_ops), nb_jours=int(nb_jours),
        )
        r = bilan_refroidissement(params)
        mode_calc = "refroid"

    st.session_state["resultats"]   = r
    st.session_state["params"]      = params
    st.session_state["mode_calc"]   = mode_calc
    st.session_state["historique"].append({
        "produit": produit_choix, "mode": r["mode"],
        "Q_kJ": round(r["Q_totale_kJ"], 1),
        "P_kW": round(r["P_utile_kW"], 2),
        "Coût/op (MAD)": round(r["cout_operation"], 3),
        "Coût annuel (MAD)": round(r["cout_annuel"], 1),
    })

r = st.session_state.get("resultats")

# ─────────────────────────────────────────────────────────────────────────────
# ONGLETS PRINCIPAUX
# ─────────────────────────────────────────────────────────────────────────────

tabs = st.tabs([
    "Résultats",
    "Analyse de sensibilité",
    "Comparaison scénarios",
    "Profil thermique",
    "Équations",
    "Interprétation",
    "Rapport & Export",
    "Historique",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RÉSULTATS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    if r is None:
        st.info("Saisir les paramètres dans la barre latérale, puis cliquer sur **Lancer les calculs**.")
    else:
        st.markdown(f'<div class="section-badge">Mode : {r["mode"]}</div>', unsafe_allow_html=True)
        st.markdown("### Indicateurs clés de performance")

        # ── Ligne 1 : Énergie ─────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Énergie utile</div>
              <div class="kpi-value">{r['Q_totale_kJ']/1000:.2f}</div>
              <div class="kpi-unit">MJ</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Puissance utile</div>
              <div class="kpi-value">{r['P_utile_kW']:.2f}</div>
              <div class="kpi-unit">kW</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="kpi-card kpi-card-warn">
              <div class="kpi-label">Puissance électrique</div>
              <div class="kpi-value">{r['P_elec_kW']:.2f}</div>
              <div class="kpi-unit">kW</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Énergie consommée</div>
              <div class="kpi-value">{r['E_elec_kWh']:.3f}</div>
              <div class="kpi-unit">kWh/opération</div>
            </div>""", unsafe_allow_html=True)

        # ── Ligne 2 : Coûts ───────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="kpi-card kpi-card-accent">
              <div class="kpi-label">Coût / opération</div>
              <div class="kpi-value">{r['cout_operation']:.3f}</div>
              <div class="kpi-unit">MAD</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="kpi-card kpi-card-accent">
              <div class="kpi-label">Coût / kg produit</div>
              <div class="kpi-value">{r['cout_kg']:.5f}</div>
              <div class="kpi-unit">MAD/kg</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="kpi-card kpi-card-accent">
              <div class="kpi-label">Coût journalier</div>
              <div class="kpi-value">{r['cout_journalier']:.2f}</div>
              <div class="kpi-unit">MAD/jour</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="kpi-card kpi-card-warn">
              <div class="kpi-label">Coût annuel</div>
              <div class="kpi-value">{r['cout_annuel']:,.0f}</div>
              <div class="kpi-unit">MAD/an</div>
            </div>""", unsafe_allow_html=True)

        # ── Temps minimal ─────────────────────────────────────────────────────
        if r.get("t_min_h"):
            st.info(
                f"**Temps minimal de traitement** avec la puissance disponible : "
                f"**{r['t_min_h']:.2f} h** ({r['t_min_h']*60:.0f} min)"
            )

        # ── Bilan énergétique détaillé ─────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Bilan énergétique détaillé")
        col_a, col_b = st.columns([1, 1])

        with col_a:
            df_bilan = pd.DataFrame({
                "Phase": [
                    "Chaleur sensible (avant congélation)",
                    "Chaleur latente (changement d'état)",
                    "Chaleur sensible (après congélation)",
                    "TOTAL",
                ],
                "Énergie (kJ)": [
                    round(r["Q_sensible_kJ"], 1),
                    round(r["Q_latente_kJ"], 1),
                    round(r["Q_post_kJ"], 1),
                    round(r["Q_totale_kJ"], 1),
                ],
                "Énergie (kWh)": [
                    round(r["Q_sensible_kJ"]/3600, 4),
                    round(r["Q_latente_kJ"]/3600, 4),
                    round(r["Q_post_kJ"]/3600, 4),
                    round(r["Q_totale_kWh"], 4),
                ],
            })
            st.table(df_bilan)
        with col_b:
            # Graphique camembert si congélation
            if r["Q_latente_kJ"] > 0:
                labels = ["Chaleur sensible (avant)", "Chaleur latente", "Chaleur sensible (après)"]
                values = [r["Q_sensible_kJ"], r["Q_latente_kJ"], r["Q_post_kJ"]]
                fig_pie = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.45,
                    marker_colors=["#2e86c1", "#1abc9c", "#5dade2"],
                    textinfo="label+percent",
                ))
                fig_pie.update_layout(
                    title="Répartition de l'énergie extraite",
                    showlegend=False, height=300, margin=dict(t=40, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        if r["Q_latente_kJ"] == 0:
            st.caption("Mode refroidissement simple — pas de changement d'état.")

        # ── Tableau synthèse coûts ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Synthèse économique")
        df_couts = pd.DataFrame({
            "Horizon": ["Par opération", "Par kg", "Journalier", "Mensuel", "Annuel"],
            "Coût (MAD)": [
                round(r["cout_operation"], 3),
                round(r["cout_kg"], 5),
                round(r["cout_journalier"], 2),
                round(r["cout_mensuel"], 2),
                round(r["cout_annuel"], 1),
            ],
        })
        st.dataframe(df_couts, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYSE DE SENSIBILITÉ
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    if r is None:
        st.info("Veuillez d'abord lancer les calculs.")
    else:
        params = st.session_state["params"]
        mode_calc = st.session_state["mode_calc"]
        st.markdown("### Analyse de sensibilité — Variation des paramètres clés")
        st.caption("Chaque graphique montre l'effet d'un paramètre sur les indicateurs énergétiques et économiques.")

        # ── COP ──────────────────────────────────────────────────────────────
        with st.expander("Effet du COP sur la consommation et le coût", expanded=True):
            cops = np.linspace(1.0, 7.0, 40)
            if mode_calc == "congelation":
                df_cop = sensibilite_COP(params, cops)
            else:
                rows = []
                for cop in cops:
                    p_tmp = ParamsRefroidissement(**{**params.__dict__, "COP": cop})
                    r_tmp = bilan_refroidissement(p_tmp)
                    rows.append({"COP": cop, "P_elec_kW": r_tmp["P_elec_kW"],
                                 "E_elec_kWh": r_tmp["E_elec_kWh"],
                                 "Coût/opération (MAD)": r_tmp["cout_operation"],
                                 "Coût annuel (MAD)": r_tmp["cout_annuel"]})
                df_cop = pd.DataFrame(rows)

            fig_cop = make_subplots(rows=1, cols=2,
                                    subplot_titles=["Puissance électrique vs COP",
                                                    "Coût annuel vs COP"])
            fig_cop.add_trace(go.Scatter(x=df_cop["COP"], y=df_cop["P_elec_kW"],
                mode="lines+markers", name="P élec (kW)",
                line=dict(color="#2e86c1", width=2)), row=1, col=1)
            fig_cop.add_trace(go.Scatter(x=df_cop["COP"], y=df_cop["Coût annuel (MAD)"],
                mode="lines+markers", name="Coût annuel (MAD)",
                line=dict(color="#e74c3c", width=2)), row=1, col=2)
            fig_cop.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)",
                                  showlegend=False,
                                  xaxis_title="COP", xaxis2_title="COP",
                                  yaxis_title="kW", yaxis2_title="MAD/an")
            st.plotly_chart(fig_cop, use_container_width=True)
            st.dataframe(df_cop.round(3), use_container_width=True, hide_index=True)

        # ── Température finale ────────────────────────────────────────────────
        with st.expander("Effet de la température finale", expanded=False):
            T_range = np.linspace(-35.0, T_ini - 1, 40)
            if mode_calc == "congelation":
                df_T = sensibilite_T_finale(params, T_range)
            else:
                rows = []
                for T in T_range:
                    if T >= T_ini:
                        continue
                    p_tmp = ParamsRefroidissement(**{**params.__dict__, "T_finale": T})
                    r_tmp = bilan_refroidissement(p_tmp)
                    rows.append({"T_finale (°C)": T, "Q_totale_kJ": r_tmp["Q_totale_kJ"],
                                 "P_utile_kW": r_tmp["P_utile_kW"],
                                 "E_elec_kWh": r_tmp["E_elec_kWh"],
                                 "Coût/opération (MAD)": r_tmp["cout_operation"]})
                df_T = pd.DataFrame(rows)

            fig_T = px.line(df_T, x="T_finale (°C)", y="Coût/opération (MAD)",
                            title="Coût d'opération en fonction de la température finale",
                            markers=True, color_discrete_sequence=["#1abc9c"])
            fig_T.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_T, use_container_width=True)

            fig_T2 = px.line(df_T, x="T_finale (°C)", y="P_utile_kW",
                             title="Puissance frigorifique utile vs Température finale",
                             markers=True, color_discrete_sequence=["#2e86c1"])
            fig_T2.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_T2, use_container_width=True)

        # ── Masse ─────────────────────────────────────────────────────────────
        with st.expander("Effet de la masse du produit", expanded=False):
            masses = np.linspace(50, masse * 3, 40)
            if mode_calc == "congelation":
                df_m = sensibilite_masse(params, masses)
            else:
                rows = []
                for m in masses:
                    p_tmp = ParamsRefroidissement(**{**params.__dict__, "masse": m})
                    r_tmp = bilan_refroidissement(p_tmp)
                    rows.append({"Masse (kg)": m, "Q_totale_kJ": r_tmp["Q_totale_kJ"],
                                 "P_utile_kW": r_tmp["P_utile_kW"],
                                 "E_elec_kWh": r_tmp["E_elec_kWh"],
                                 "Coût/opération (MAD)": r_tmp["cout_operation"]})
                df_m = pd.DataFrame(rows)

            fig_m = px.line(df_m, x="Masse (kg)", y="P_utile_kW",
                            title="Puissance utile en fonction de la masse",
                            markers=False, color_discrete_sequence=["#8e44ad"])
            fig_m.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_m, use_container_width=True)

        # ── Prix électricité ──────────────────────────────────────────────────
        with st.expander("Effet du prix de l'électricité", expanded=False):
            prix_range = np.linspace(0.05, 0.40, 40)
            if mode_calc == "congelation":
                df_px = sensibilite_prix_elec(params, prix_range)
            else:
                r_base = bilan_refroidissement(params)
                rows = []
                for px_ in prix_range:
                    cout_op = r_base["E_elec_kWh"] * px_
                    rows.append({
                        "Prix élec (MAD/kWh)": px_,
                        "Coût/opération (MAD)": cout_op,
                        "Coût annuel (MAD)": cout_op * nb_ops * nb_jours,
                    })
                df_px = pd.DataFrame(rows)

            fig_px = px.area(df_px, x="Prix élec (MAD/kWh)", y="Coût annuel (MAD)",
                             title="Coût annuel selon le tarif électrique",
                             color_discrete_sequence=["#e74c3c"])
            fig_px.update_layout(height=350, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_px, use_container_width=True)

        # ── Durée ─────────────────────────────────────────────────────────────
        with st.expander("Effet de la durée de traitement sur la puissance", expanded=False):
            durees = np.linspace(0.5, 24.0, 40)
            if mode_calc == "congelation":
                df_d = sensibilite_duree(params, durees)
            else:
                rows = []
                for d in durees:
                    p_tmp = ParamsRefroidissement(**{**params.__dict__, "duree": d})
                    r_tmp = bilan_refroidissement(p_tmp)
                    rows.append({"Durée (h)": d, "P_utile_kW": r_tmp["P_utile_kW"],
                                 "P_elec_kW": r_tmp["P_elec_kW"],
                                 "E_elec_kWh": r_tmp["E_elec_kWh"]})
                df_d = pd.DataFrame(rows)

            fig_d = make_subplots(rows=1, cols=2,
                                  subplot_titles=["Puissance utile vs Durée",
                                                  "Puissance électrique vs Durée"])
            fig_d.add_trace(go.Scatter(x=df_d["Durée (h)"], y=df_d["P_utile_kW"],
                mode="lines", line=dict(color="#2e86c1", width=2)), row=1, col=1)
            fig_d.add_trace(go.Scatter(x=df_d["Durée (h)"], y=df_d["P_elec_kW"],
                mode="lines", line=dict(color="#e74c3c", width=2)), row=1, col=2)
            fig_d.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                                 showlegend=False,
                                 xaxis_title="Durée (h)", xaxis2_title="Durée (h)",
                                 yaxis_title="kW", yaxis2_title="kW")
            st.plotly_chart(fig_d, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPARAISON DE SCÉNARIOS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### Comparaison de scénarios prédéfinis")
    st.caption("Comparez plusieurs configurations : COP, températures finales, masses, durées.")

    if r is None:
        st.info("Veuillez d'abord lancer un calcul de base.")
    else:
        params = st.session_state["params"]
        mode_calc = st.session_state["mode_calc"]
        base = params.__dict__.copy()

        # Construction des scénarios comparatifs
        if mode_calc == "congelation":
            scenarios_def = [
                {**base, "nom": "Référence (COP 3.0)", "mode": "congelation"},
                {**base, "nom": "COP élevé (4.5)", "mode": "congelation", "COP": 4.5},
                {**base, "nom": "COP faible (1.8)", "mode": "congelation", "COP": 1.8},
                {**base, "nom": "T finale -25°C", "mode": "congelation", "T_finale": -25.0},
                {**base, "nom": "Double masse (x2)", "mode": "congelation", "masse": base["masse"] * 2},
                {**base, "nom": "Durée courte (4h)", "mode": "congelation", "duree": 4.0},
            ]
        else:
            scenarios_def = [
                {**base, "nom": "Référence", "mode": "refroid"},
                {**base, "nom": "COP élevé (4.5)", "mode": "refroid", "COP": 4.5},
                {**base, "nom": "COP faible (1.8)", "mode": "refroid", "COP": 1.8},
                {**base, "nom": "T finale 2°C", "mode": "refroid", "T_finale": 2.0},
                {**base, "nom": "Double masse (x2)", "mode": "refroid", "masse": base["masse"] * 2},
                {**base, "nom": "Durée courte (2h)", "mode": "refroid", "duree": 2.0},
            ]

        # Nettoyage des clés inutiles pour chaque scénario
        sc_clean = []
        allowed_refroid = set(ParamsRefroidissement.__dataclass_fields__.keys()) | {"nom", "mode"}
        allowed_cong    = set(ParamsCongélation.__dataclass_fields__.keys()) | {"nom", "mode"}

        for sc in scenarios_def:
            sc_copy = {k: v for k, v in sc.items()
                       if k in (allowed_cong if sc["mode"] == "congelation" else allowed_refroid)}
            sc_clean.append(sc_copy)

        df_comp = comparer_scenarios(sc_clean)

        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        # Graphique comparatif
        fig_comp = make_subplots(rows=1, cols=3,
            subplot_titles=["Puissance électrique (kW)", "Énergie (kWh)", "Coût annuel (MAD)"])

        colors = px.colors.qualitative.Set2
        for i, sc_name in enumerate(df_comp["Scénario"]):
            color = colors[i % len(colors)]
            fig_comp.add_trace(go.Bar(
                x=[sc_name], y=[df_comp.loc[i, "P électrique (kW)"]],
                name=sc_name, marker_color=color, showlegend=(i == 0),
            ), row=1, col=1)
            fig_comp.add_trace(go.Bar(
                x=[sc_name], y=[df_comp.loc[i, "E électrique (kWh)"]],
                name=sc_name, marker_color=color, showlegend=False,
            ), row=1, col=2)
            fig_comp.add_trace(go.Bar(
                x=[sc_name], y=[df_comp.loc[i, "Coût annuel (MAD)"]],
                name=sc_name, marker_color=color, showlegend=False,
            ), row=1, col=3)

        fig_comp.update_layout(
            height=420, barmode="group",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            xaxis=dict(showticklabels=False),
            xaxis2=dict(showticklabels=False),
            xaxis3=dict(showticklabels=False),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Recommandation
        reco = recommander_scenario(df_comp)
        st.markdown(f'<div class="interp-box">{reco}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROFIL THERMIQUE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("### Profil de température dans le temps")
    if r is None:
        st.info("Veuillez d'abord lancer les calculs.")
    else:
        params = st.session_state["params"]
        mode_calc = st.session_state["mode_calc"]

        T_cong_plot = getattr(params, "T_congelation", -1.5)
        df_profil = profil_temperature(
            T_ini=params.T_initiale,
            T_cong=T_cong_plot if mode_calc == "congelation" else params.T_finale + 1,
            T_fin=params.T_finale,
            duree_h=params.duree,
        )

        fig_prof = go.Figure()
        fig_prof.add_trace(go.Scatter(
            x=df_profil["Temps (h)"], y=df_profil["Température (°C)"],
            mode="lines", name="Température produit",
            line=dict(color="#2e86c1", width=3),
            fill="tozeroy", fillcolor="rgba(46,134,193,0.10)",
        ))

        # Lignes horizontales de référence
        fig_prof.add_hline(y=params.T_initiale, line_dash="dash",
                           line_color="#e74c3c", annotation_text=f"T₀ = {params.T_initiale}°C")
        fig_prof.add_hline(y=params.T_finale, line_dash="dash",
                           line_color="#1abc9c", annotation_text=f"T_fin = {params.T_finale}°C")
        if mode_calc == "congelation":
            fig_prof.add_hline(y=T_cong_plot, line_dash="dot",
                               line_color="#8e44ad", annotation_text=f"T_cong = {T_cong_plot}°C")
            # Zone de congélation
            fig_prof.add_vrect(
                x0=params.duree * 0.35, x1=params.duree * 0.65,
                fillcolor="rgba(142,68,211,0.08)", line_width=0,
                annotation_text="Palier de congélation", annotation_position="top left",
            )

        fig_prof.update_layout(
            title="Évolution de la température du produit au cours du traitement",
            xaxis_title="Temps (h)", yaxis_title="Température (°C)",
            height=450, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,249,250,1)",
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor="#dee2e6"),
            yaxis=dict(showgrid=True, gridcolor="#dee2e6"),
        )
        st.plotly_chart(fig_prof, use_container_width=True)
        st.caption("Note : Le profil est une modélisation simplifiée (décroissance exponentielle + palier). Un modèle de diffusion thermique complet nécessiterait la géométrie exacte du produit.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ÉQUATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("### Modèle mathématique — Équations utilisées")
    st.markdown("""
<div class="section-badge">Thermodynamique appliquée — IAA</div>

Les équations ci-dessous constituent le noyau du modèle de calcul. Elles sont issues
des bilans thermodynamiques classiques appliqués aux procédés agroalimentaires.
""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Bilan matière")
        st.latex(r'm_{\text{produit}} = m_{\text{entrée}} \quad (\text{système fermé par lot})')

        st.markdown("#### Phase 1 — Chaleur sensible (avant congélation)")
        st.latex(r'Q_1 = m \cdot c_{p,\text{frais}} \cdot (T_{\text{ini}} - T_{\text{cong}}) \quad [\text{kJ}]')

        st.markdown("#### Phase 2 — Chaleur latente de congélation")
        st.latex(r'Q_2 = m \cdot w_{\text{eau}} \cdot L_{\text{cong}} \quad [\text{kJ}]')
        st.markdown("où $w_{\\text{eau}}$ = fraction d'eau congelable")

        st.markdown("#### Phase 3 — Chaleur sensible (après congélation)")
        st.latex(r'Q_3 = m \cdot c_{p,\text{congelé}} \cdot (T_{\text{cong}} - T_{\text{finale}}) \quad [\text{kJ}]')

        st.markdown("#### Énergie totale à extraire")
        st.latex(r'Q_{\text{totale}} = Q_1 + Q_2 + Q_3 \quad [\text{kJ}]')

    with col2:
        st.markdown("#### Puissance frigorifique utile")
        st.latex(r'P_{\text{utile}} = \frac{Q_{\text{totale}}}{\Delta t \times 3600} \quad [\text{kW}]')
        st.markdown("$\Delta t$ en heures")

        st.markdown("#### Machine frigorifique — COP")
        st.latex(r'\text{COP} = \frac{Q_{\text{froid}}}{W_{\text{élec}}} \implies P_{\text{élec}} = \frac{P_{\text{utile}}}{\text{COP}} \quad [\text{kW}]')

        st.markdown("#### Énergie électrique consommée")
        st.latex(r'E_{\text{élec}} = P_{\text{élec}} \times \Delta t \quad [\text{kWh}]')

        st.markdown("#### Coût énergétique")
        st.latex(r'\text{Coût} = E_{\text{élec}} \times p_{\text{élec}} \quad [\text{MAD}]')
        st.markdown("$p_{\\text{élec}}$ : tarif en MAD/kWh")

        st.markdown("#### Temps minimal (puissance imposée)")
        st.latex(r't_{\text{min}} = \frac{Q_{\text{totale}}}{P_{\text{dispo}} \times 3600} \quad [\text{h}]')

    st.markdown("---")
    st.markdown("#### Hypothèses du modèle")
    st.markdown("""
- Propriétés thermophysiques **constantes** par phase (cp, L)
- Système **fermé** (traitement par lot)
- Régime **transitoire** — puissance moyenne sur la durée totale
- **Pas de pertes thermiques** aux parois (bilan utile pur)
- COP considéré **constant** (machine à vitesse fixe)
- La fraction d'eau congelable `w_eau` est supposée **constante** et indépendante de la température
""")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — INTERPRÉTATION
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("### Interprétation automatique des résultats")
    if r is None:
        st.info("Veuillez d'abord lancer les calculs.")
    else:
        mode_calc = st.session_state["mode_calc"]
        interpretations = interpreter_resultats(r, mode_calc)
        for texte in interpretations:
            st.markdown(f'<div class="interp-box">{texte}</div>', unsafe_allow_html=True)
            st.markdown("")

        # Radar chart — performance globale
        st.markdown("---")
        st.markdown("#### Radar de performance du procédé")

        # Scores normalisés (0→10)
        score_cop       = min(10, r["COP"] / 7.0 * 10)
        score_puissance = max(0, 10 - min(10, r["P_utile_kW"] / 100 * 10))
        score_cout_kg   = max(0, 10 - min(10, r["cout_kg"] / 0.2 * 10))
        score_energie   = max(0, 10 - min(10, r["E_elec_kWh"] / 500 * 10))
        score_rentab    = max(0, 10 - min(10, r["cout_annuel"] / 50000 * 10))

        categories = ["COP machine", "Puissance maîtrisée",
                      "Coût/kg faible", "Énergie faible", "Rentabilité annuelle"]
        values_radar = [score_cop, score_puissance, score_cout_kg,
                        score_energie, score_rentab]
        values_radar += values_radar[:1]
        categories_plot = categories + [categories[0]]

        fig_radar = go.Figure(go.Scatterpolar(
            r=values_radar, theta=categories_plot,
            fill="toself", fillcolor="rgba(46,134,193,0.2)",
            line=dict(color="#2e86c1", width=2),
            name="Performance",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10],
                                       tickfont=dict(size=9))),
            showlegend=False, height=400,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.caption("Score normalisé sur 10 — plus élevé = meilleure performance sur ce critère.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — RAPPORT & EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown("### Rapport & Export")
    if r is None:
        st.info("Veuillez d'abord lancer les calculs.")
    else:
        params = st.session_state["params"]
        mode_calc = st.session_state["mode_calc"]
        interpretations = interpreter_resultats(r, mode_calc)

        params_dict = {
            "Produit" : produit_choix,
            "Mode" : r["mode"],
            "Masse (kg)" : params.masse,
            "T initiale (°C)" : params.T_initiale,
            "T finale (°C)" : params.T_finale,
            "Cp frais (kJ/kg·K)" : params.cp_produit,
            "Durée (h)" : params.duree,
            "COP" : params.COP,
            "Prix élec (MAD/kWh)" : params.prix_elec,
            "Nb opérations/jour" : params.nb_operations,
            "Nb jours/an" : params.nb_jours,
        }

        rapport_md = generer_rapport_markdown(params_dict, r, interpretations)

        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.markdown("#### Aperçu du rapport")
            st.markdown(rapport_md)

        with col_right:
            st.markdown("#### Téléchargements")

            # ── Export Excel ────────────────────────────────────────────────
            # Sensibilité pour export
            cops_arr = np.linspace(1.0, 7.0, 20)
            T_arr    = np.linspace(-35.0, params.T_initiale - 1, 20)
            if mode_calc == "congelation":
                df_sensi = {
                    "Variation COP": sensibilite_COP(params, cops_arr),
                    "Variation T finale": sensibilite_T_finale(params, T_arr),
                    "Variation masse": sensibilite_masse(params, np.linspace(50, params.masse*3, 20)),
                    "Variation prix élec": sensibilite_prix_elec(params, np.linspace(0.05, 0.40, 20)),
                }
            else:
                rows_cop = []
                for cop in cops_arr:
                    p_tmp = ParamsRefroidissement(**{**params.__dict__, "COP": cop})
                    r_tmp = bilan_refroidissement(p_tmp)
                    rows_cop.append({"COP": cop, "P_elec_kW": r_tmp["P_elec_kW"],
                                     "Coût annuel (MAD)": r_tmp["cout_annuel"]})
                df_sensi = {
                    "Variation COP": pd.DataFrame(rows_cop),
                }

            # Scénarios pour export
            base = params.__dict__.copy()
            allowed = set(ParamsCongélation.__dataclass_fields__.keys() if mode_calc == "congelation"
                          else ParamsRefroidissement.__dataclass_fields__.keys()) | {"nom", "mode"}
            if mode_calc == "congelation":
                sc_export = [
                    {k: v for k, v in {**base, "nom": "Référence", "mode": "congelation"}.items() if k in allowed},
                    {k: v for k, v in {**base, "nom": "COP 4.5", "mode": "congelation", "COP": 4.5}.items() if k in allowed},
                ]
            else:
                sc_export = [
                    {k: v for k, v in {**base, "nom": "Référence", "mode": "refroid"}.items() if k in allowed},
                    {k: v for k, v in {**base, "nom": "COP 4.5", "mode": "refroid", "COP": 4.5}.items() if k in allowed},
                ]
            df_sc = comparer_scenarios(sc_export)

            xlsx_bytes = exporter_excel(params_dict, r, df_sensi, df_sc, interpretations)
            st.download_button(
                label="Télécharger Excel (.xlsx)",
                data=xlsx_bytes,
                file_name="ThermoIAA_resultats.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

            # ── Export PDF ──────────────────────────────────────────────────
            pdf_bytes = exporter_pdf(rapport_md)
            if pdf_bytes:
                st.download_button(
                    label="Télécharger rapport PDF",
                    data=pdf_bytes,
                    file_name="ThermoIAA_rapport.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            # ── Export rapport Markdown ─────────────────────────────────────
            st.download_button(
                label="Télécharger rapport Markdown",
                data=rapport_md.encode("utf-8"),
                file_name="ThermoIAA_rapport.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — HISTORIQUE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("### Historique des simulations")
    historique = st.session_state.get("historique", [])
    if not historique:
        st.info("Aucune simulation effectuée dans cette session.")
    else:
        df_hist = pd.DataFrame(historique)
        df_hist.index = df_hist.index + 1
        df_hist.index.name = "N°"
        st.dataframe(df_hist, use_container_width=True)

        if st.button("Effacer l'historique"):
            st.session_state["historique"] = []
            st.rerun()


# ── Footer — REMOVED (was appearing as red error message) ──────────────────────
# st.markdown("---")
# st.markdown(
#     "<div style='text-align:center; color:#aaa; font-size:.8rem;'>"
#     "ThermoIAA v1.0 — Projet Thermodynamique Appliquée · Industrie Agroalimentaire · 2024/2025"
#     "</div>",
#     unsafe_allow_html=True,
# )
