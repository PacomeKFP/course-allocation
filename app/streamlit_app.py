"""App Streamlit — upload, résolution, exploration, export.

Onglets : Résumé · Non affectés · Remplissage · Stats par demande ·
Compensation. Bloc tendu (n_enrolled > cap_max) mis en rouge.
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from src.data import build_campaign
from src.rules import Feasibility
from src.solvers import PriorityChain, MipSolver
from src.reporting import Report, export_synapse_import

st.set_page_config(page_title="Course allocation — Télécom Paris",
                   page_icon="🎓", layout="wide")
st.title("🎓 Affectation des cours électifs de 2A")


def _save_upload(uploaded) -> str | None:
    if uploaded is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    tmp.write(uploaded.read()); tmp.close()
    return tmp.name


with st.sidebar:
    st.header("Entrées")
    up_students = st.file_uploader("Étudiants (CSV Synapse)", type=["csv"])
    up_campaign = st.file_uploader("Campagne de vœux (CSV Synapse)", type=["csv"])
    up_ecue = st.file_uploader("Liste ECUE (optionnel)", type=["csv"])
    cost_power = st.slider("Puissance du coût (rang^p)", 1, 4, 2)
    time_limit = st.slider("Time limit MIP (s)", 5, 300, 60)
    run = st.button("Lancer l'affectation", type="primary",
                    disabled=not (up_students and up_campaign))

if not run:
    st.info("Charge les deux CSV obligatoires (étudiants + campagne).")
    st.stop()

with st.spinner("Chargement…"):
    campaign = build_campaign(
        _save_upload(up_students), _save_upload(up_campaign), _save_upload(up_ecue))
st.success(f"{len(campaign.students)} étudiants, {len(campaign.occurrences)} occurrences, "
           f"{len(campaign.voeux)} vœux non-vides, {len(campaign.demandes())} demandes")

with st.spinner("Priorités…"):
    pre = PriorityChain().apply(campaign)
with st.spinner("Optimisation MIP…"):
    assignment = MipSolver(cost_power=cost_power,
                           time_limit_s=time_limit).solve(campaign, pre_assignment=pre)
report = Report(campaign, assignment)
stats = report.stats_global()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Taux d'affectation", f"{stats['assignment_rate']*100:.1f}%")
c2.metric("1er choix", f"{stats['first_choice_share']*100:.1f}%")
c3.metric("Top-3", f"{stats['top3_share']*100:.1f}%")
c4.metric("Affectations", stats['n_assigned'])

tabs = st.tabs(["Résumé", "Non affectés", "Remplissage", "Par demande",
                "Compensation", "Export"])

with tabs[0]:
    st.subheader("Distribution des rangs obtenus")
    dist = stats["rank_distribution"]
    st.bar_chart(pd.DataFrame({"count": dist}))

with tabs[1]:
    na = report.not_assigned()
    st.write(f"**{len(na)}** paires (élève, demande) non affectées.")
    st.dataframe(na, use_container_width=True, hide_index=True)

with tabs[2]:
    df = report.filling()
    def highlight(row):
        color = "background-color: #fecaca" if row["over_max"] else \
                "background-color: #fef3c7" if row["under_min"] else ""
        return [color] * len(row)
    st.dataframe(df.style.apply(highlight, axis=1),
                 use_container_width=True, hide_index=True)

with tabs[3]:
    st.dataframe(report.stats_per_demande(), use_container_width=True, hide_index=True)

with tabs[4]:
    st.dataframe(report.stats_compensation().sort_values("worst_rank", ascending=False),
                 use_container_width=True, hide_index=True)

with tabs[5]:
    out = Path(tempfile.gettempdir()) / "synapse_import.csv"
    export_synapse_import(campaign, assignment, out)
    st.download_button("⬇️ Télécharger synapse_import.csv",
                       data=out.read_bytes(), file_name="synapse_import.csv",
                       mime="text/csv")
