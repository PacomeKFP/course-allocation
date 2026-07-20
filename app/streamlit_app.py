"""App Streamlit — affectation des cours électifs de 2A.

Contrôleur principal : chargement des CSV, exécution du pipeline,
persistance en session (pour éviter le reset après download), délégation
du rendu à ``views.py``.
"""
from __future__ import annotations
import sys, tempfile
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.data import build_campaign
from src.solvers import PriorityChain, MipSolver
from src.reporting import Report
from app import views

st.set_page_config(page_title="Affectation cours 2A — Télécom Paris",
                   page_icon="🎓", layout="wide")
st.title("🎓 Affectation des cours électifs de 2A")
st.caption("Chargez les fichiers Synapse, lancez le solveur, explorez le rapport, "
           "téléchargez les sorties.")


@dataclass
class State:
    campaign: object
    assignment: dict
    report: Report
    stats: dict


def _save(uploaded) -> str | None:
    if uploaded is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.write(uploaded.read()); tmp.close()
    return tmp.name


with st.sidebar:
    st.header("1. Charger les fichiers")
    up_students = st.file_uploader("Liste des étudiants (CSV)", type=["csv"],
                                   help="Format Synapse : etudiants_anonymises.csv")
    up_campaign = st.file_uploader("Vœux de la campagne (CSV)", type=["csv"],
                                   help="Format Synapse : structure-export")
    up_ecue = st.file_uploader("Liste ECUE (optionnel)", type=["csv"],
                               help="Sinon la version embarquée par défaut est utilisée")

    st.header("2. Paramètres")
    cost_power = st.slider("Puissance du coût (rang^p)", 1, 4, 2,
                           help="Plus grand = pénalise plus fort les rangs éloignés. "
                                "2 = quadratique (recommandé).")
    time_limit = st.slider("Temps max solveur (s)", 5, 300, 60)

    st.header("3. Lancer")
    run = st.button("▶️ Résoudre l'affectation", type="primary",
                    use_container_width=True,
                    disabled=not (up_students and up_campaign))
    if "state" in st.session_state:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            del st.session_state.state
            st.rerun()

if run:
    with st.spinner("Chargement des CSV…"):
        c = build_campaign(_save(up_students), _save(up_campaign), _save(up_ecue))
    with st.spinner("Application des priorités (anglophones, apprentis)…"):
        pre = PriorityChain().apply(c)
    with st.spinner(f"Optimisation MIP (max {time_limit}s)…"):
        a = MipSolver(cost_power=cost_power, time_limit_s=time_limit).solve(c, pre_assignment=pre)
    r = Report(c, a)
    st.session_state.state = State(c, a, r, r.stats_global())
    st.rerun()

if "state" not in st.session_state:
    st.info("👈 Charge les deux CSV obligatoires (étudiants + campagne) dans la barre "
            "latérale, ajuste les paramètres, puis clique sur « Résoudre ».")
    st.stop()

state = st.session_state.state
st.success(f"✅ {len(state.campaign.students)} étudiants · "
           f"{len(state.campaign.occurrences)} occurrences · "
           f"{len(state.campaign.voeux)} vœux non-vides · "
           f"{len(state.campaign.demandes())} demandes")

tabs = st.tabs(["📊 Vue d'ensemble", "❌ Non affectés", "📦 Remplissage",
                "📈 Par demande", "⚖️ Compensation", "⬇️ Export"])
with tabs[0]: views.summary(state)
with tabs[1]: views.not_assigned(state)
with tabs[2]: views.filling(state)
with tabs[3]: views.per_demande(state)
with tabs[4]: views.compensation(state)
with tabs[5]: views.export(state)
