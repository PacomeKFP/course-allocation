"""Rendus par onglet — chaque fonction assume ``st.session_state.report``.

Sépare la logique d'affichage du contrôleur principal pour garder
``streamlit_app.py`` sous 100 lignes.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.solvers.base import rank
from . import labels as L


def _translate_period_col(df: pd.DataFrame) -> pd.DataFrame:
    if "period" in df.columns:
        df = df.assign(period=df["period"].map(L.fmt_period))
    return df


def summary(state):
    st.subheader("Vue d'ensemble", help="Métriques clés de l'affectation")
    s = state.stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Taux d'affectation", f"{s['assignment_rate']*100:.1f}%",
              help=f"{s['n_assigned']} paires (élève, demande) affectées sur {s['n_expected']}")
    c2.metric("Premier choix", f"{s['first_choice_share']*100:.1f}%",
              help="Part des affectations où l'élève obtient son vœu n°1")
    c3.metric("Top-3", f"{s['top3_share']*100:.1f}%",
              help="Part des affectations où l'élève obtient l'un de ses 3 premiers vœux")
    c4.metric("Affectations", s["n_assigned"])

    st.subheader("Distribution des rangs obtenus",
                 help="Combien d'affectations ont été faites à chaque rang de préférence")
    dist = pd.DataFrame({"Rang obtenu": [f"#{k}" for k in s["rank_distribution"]],
                        "Nombre d'affectations": list(s["rank_distribution"].values())})
    st.bar_chart(dist, x="Rang obtenu", y="Nombre d'affectations")


def not_assigned(state):
    df = state.report.not_assigned()
    st.info(f"**{len(df)}** paires (élève, demande) non affectées. La colonne "
            "« Cause probable » indique l'étape où l'attribution a échoué.")
    st.dataframe(df, column_config=L.NOT_ASSIGNED, use_container_width=True, hide_index=True)


def filling(state):
    df = _translate_period_col(state.report.filling())
    st.info("Cliquez sur une ligne pour voir les étudiants admis dans l'occurrence. "
            "🟠 sous l'effectif minimum · 🔴 dépasse l'effectif maximum.")
    def _style(row):
        if row["over_max"]: return ["background-color: #fecaca"] * len(row)
        if row["under_min"]: return ["background-color: #fef3c7"] * len(row)
        return [""] * len(row)
    sel = st.dataframe(df.style.apply(_style, axis=1),
                       column_config=L.FILLING, use_container_width=True,
                       hide_index=True, on_select="rerun", selection_mode="single-row")
    if sel and sel.selection.rows:
        _show_enrolled_students(state, df.iloc[sel.selection.rows[0]]["id_occ"])


def _show_enrolled_students(state, id_occ):
    o = state.campaign.occurrences[id_occ]
    st.markdown(f"**Étudiants admis dans** `{o.code_ue}` — {o.label}")
    rows = []
    for (sid, did), oid in state.assignment.items():
        if oid == id_occ:
            s = state.campaign.students.get(sid)
            v = state.campaign.voeu_of(sid, did)
            rows.append({"Élève": sid, "Régime": L.REGIME_LABEL.get(s.regime, s.regime) if s else "",
                         "Francophone": "OUI" if s and s.francophone else "NON",
                         "Filière(s)": "+".join(s.filieres) if s else "",
                         "Rang obtenu": f"#{rank(v, id_occ)}" if v else "?"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def per_demande(state):
    st.info("Une ligne par demande (bloc). « Rang moyen » de 1.05 signifie que "
            "la plupart des élèves ont eu leur premier choix ; ≥ 2 indique de "
            "la friction.")
    st.dataframe(state.report.stats_per_demande(),
                 column_config=L.STATS_DEMANDE, use_container_width=True, hide_index=True)


def compensation(state):
    st.info("Compensation inter-demandes : détecte les élèves systématiquement "
            "mal servis (pire rang élevé sur plusieurs demandes).")
    st.dataframe(state.report.stats_compensation().sort_values("worst_rank", ascending=False),
                 column_config=L.STATS_COMP, use_container_width=True, hide_index=True)


def export(state):
    from .export_view import render as _render_export
    _render_export(state)
