"""Interface principale — affectation des cours électifs 2A Télécom Paris."""
from __future__ import annotations
import sys, tempfile, time
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.data import build_campaign
from src.solvers import PriorityChain, MipSolver
from src.reporting import Report
from app import views
from app.theme import apply_theme, header, metric_row

st.set_page_config(page_title="Affectation des cours électifs — Télécom Paris",
                   layout="wide", initial_sidebar_state="expanded")
apply_theme()
header("Affectation des cours électifs de 2A",
       "Télécom Paris — campagne d'inscription pédagogique")


@dataclass
class State:
    campaign: object
    assignment: dict
    report: Report
    stats: dict
    solver_time_s: float


def _save(u):
    if u is None: return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.write(u.read()); tmp.close(); return tmp.name


with st.sidebar:
    st.markdown("### Fichiers en entrée")
    up_students = st.file_uploader("Liste des étudiants", type=["csv"],
                                    help="Format Synapse : etudiants_anonymises.csv")
    up_campaign = st.file_uploader("Vœux de la campagne", type=["csv"],
                                    help="Format Synapse : structure-export")
    up_ecue = st.file_uploader("Liste des occurrences (facultatif)", type=["csv"],
                                help="Sans ce fichier, la version embarquée est utilisée")
    st.markdown("### Paramètres du solveur")
    puissance = st.slider("Puissance de la pénalité de rang", 1, 4, 2,
                          help="Coût = rang^p. Plus grand p pénalise davantage les rangs éloignés.")
    temps_max = st.slider("Temps maximum du solveur (secondes)", 5, 300, 60)
    st.markdown("### Actions")
    resoudre = st.button("Lancer la résolution", type="primary",
                         use_container_width=True,
                         disabled=not (up_students and up_campaign))
    if "state" in st.session_state and st.button("Réinitialiser", use_container_width=True):
        for k in ("state", "campaign_preview"):
            st.session_state.pop(k, None)
        st.rerun()

if up_students and up_campaign and "campaign_preview" not in st.session_state:
    st.session_state.campaign_preview = build_campaign(
        _save(up_students), _save(up_campaign), _save(up_ecue))

if resoudre:
    c = st.session_state.campaign_preview
    with st.spinner("Priorités (anglophones, apprentis)…"):
        pre = PriorityChain().apply(c)
    with st.spinner(f"Optimisation (max {temps_max} s)…"):
        t0 = time.time()
        a = MipSolver(cost_power=puissance, time_limit_s=temps_max).solve(c, pre_assignment=pre)
        dt = time.time() - t0
    r = Report(c, a)
    st.session_state.state = State(c, a, r, r.stats_global(), dt)
    st.rerun()

if "state" in st.session_state:
    s = st.session_state.state
    metric_row([
        ("Étudiants", len(s.campaign.students), None),
        ("Occurrences", len(s.campaign.occurrences), None),
        ("Vœux exprimés", len(s.campaign.voeux), None),
        ("Demandes", len(s.campaign.demandes()), None),
        ("Temps d'optimisation", f"{s.solver_time_s:.1f} s",
         "Temps mis par le solveur CP-SAT (hors chargement)"),
    ])
    tabs = st.tabs(["Synthèse", "Non affectés", "Remplissage",
                    "Résultats par demande", "Équité par élève", "Export"])
    for tab, view in zip(tabs, [views.summary, views.not_assigned, views.filling,
                                 views.per_demande, views.compensation, views.export]):
        with tab: view(s)
elif "campaign_preview" in st.session_state:
    c = st.session_state.campaign_preview
    metric_row([("Étudiants", len(c.students), None),
                ("Occurrences", len(c.occurrences), None),
                ("Vœux exprimés", len(c.voeux), None),
                ("Demandes", len(c.demandes()), None)])
    st.info("Les fichiers sont chargés. Ajustez les paramètres à gauche puis "
            "cliquez sur **Lancer la résolution**.")
else:
    st.info("Chargez à gauche la liste des étudiants et l'export de la campagne "
            "de vœux Synapse pour démarrer.")
