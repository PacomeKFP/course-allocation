"""Rendus par onglet — chaque fonction assume ``state`` en argument."""
from __future__ import annotations
import pandas as pd
import streamlit as st
from src.solvers.base import rank
from . import labels as L


def _translate_period(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(period=df["period"].map(L.fmt_period)) if "period" in df.columns else df


def summary(state):
    st.markdown("#### Distribution des rangs obtenus")
    st.caption("Rang 1 = premier vœu servi, rang 2 = deuxième vœu, etc. "
               "Distribution concentrée sur les rangs faibles = affectation satisfaisante.")
    s = state.stats
    dist = pd.DataFrame({"Rang obtenu": [f"#{k}" for k in s["rank_distribution"]],
                         "Nombre d'affectations": list(s["rank_distribution"].values())})
    st.bar_chart(dist, x="Rang obtenu", y="Nombre d'affectations",
                 color="#003a6b", height=340)
    c1, c2, c3 = st.columns(3)
    c1.metric("Premier choix servi", f"{s['first_choice_share']*100:.1f} %",
              help="Part des affectations où l'élève obtient son vœu n°1")
    c2.metric("Dans le top 3", f"{s['top3_share']*100:.1f} %",
              help="Part des affectations où l'élève obtient l'un de ses 3 premiers vœux")
    c3.metric("Taux d'affectation", f"{s['assignment_rate']*100:.1f} %",
              help=f"{s['n_assigned']} paires (élève, demande) affectées "
                   f"sur {s['n_expected']} attendues")


def not_assigned(state):
    df = state.report.not_assigned()
    if df.empty:
        st.success("Toutes les paires (élève, demande) attendues ont été affectées.")
        return
    st.caption(f"{len(df)} paires non affectées — la colonne « Cause » "
               "détaille la ventilation des vœux (saturés, non accessibles, etc.).")
    st.dataframe(df, column_config=L.NOT_ASSIGNED, use_container_width=True, hide_index=True)


def filling(state):
    df = _translate_period(state.report.filling())
    st.caption("Une ligne par occurrence. Cliquez sur une ligne pour voir "
               "la liste nominative des étudiants qui y sont admis. "
               "Ligne rouge : effectif atteint dépasse le maximum. "
               "Ligne jaune : effectif atteint sous le minimum.")
    def _style(row):
        if row["over_max"]: return ["background-color: #fecaca"] * len(row)
        if row["under_min"]: return ["background-color: #fef3c7"] * len(row)
        return [""] * len(row)
    sel = st.dataframe(
        df.style.apply(_style, axis=1),
        column_config=L.FILLING, use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row")
    if sel and sel.selection.rows:
        _show_enrolled_students(state, df.iloc[sel.selection.rows[0]]["id_occ"])


def _show_enrolled_students(state, id_occ):
    o = state.campaign.occurrences[id_occ]
    st.markdown(f"##### Étudiants admis dans `{o.code_ue}` — {o.label}")
    rows = []
    for (sid, did), oid in state.assignment.items():
        if oid != id_occ:
            continue
        s = state.campaign.students.get(sid)
        v = state.campaign.voeu_of(sid, did)
        rows.append({
            "Élève": sid,
            "Régime": L.REGIME_LABEL.get(s.regime, s.regime) if s else "",
            "Francophone": "OUI" if s and s.francophone else "NON",
            "Filière(s)": "+".join(s.filieres) if s else "",
            "Rang obtenu": f"#{rank(v, id_occ)}" if v else "n/a",
        })
    if not rows:
        st.write("Aucun étudiant affecté à cette occurrence.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def per_demande(state):
    st.caption("Une ligne par demande (bloc pédagogique). « Rang moyen » "
               "proche de 1 signifie que la plupart des élèves ont obtenu "
               "leur premier vœu ; au-delà de 2, la demande présente de la friction.")
    st.dataframe(state.report.stats_per_demande(), column_config=L.STATS_DEMANDE,
                 use_container_width=True, hide_index=True)


def compensation(state):
    st.caption("Vue par élève. Trie décroissant sur « Pire rang » pour "
               "détecter les élèves systématiquement mal servis.")
    st.dataframe(
        state.report.stats_compensation().sort_values("worst_rank", ascending=False),
        column_config=L.STATS_COMP, use_container_width=True, hide_index=True)


def export(state):
    from .export_view import render
    render(state)
