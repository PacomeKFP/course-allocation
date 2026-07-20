"""Rendus par onglet — chaque fonction assume ``state`` en argument."""
from __future__ import annotations
from collections import Counter
import pandas as pd
import streamlit as st
from src.solvers.base import rank
from . import labels as L
from .charts import rank_histogram, rank_kpi_row


def _translate_period(df):
    return df.assign(period=df["period"].map(L.fmt_period)) if "period" in df.columns else df


def summary(state):
    st.markdown("#### Distribution des rangs obtenus")
    st.caption("Rang 1 = premier vœu servi, rang 2 = deuxième vœu, etc.")
    rank_histogram(state.stats["rank_distribution"], height=340)
    s = state.stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Premier choix servi", f"{s['first_choice_share']*100:.1f} %",
              help="Part des affectations où l'élève obtient son vœu n°1")
    c2.metric("Dans le top 3", f"{s['top3_share']*100:.1f} %",
              help="Part des affectations où l'élève obtient l'un de ses 3 premiers vœux")
    c3.metric("Taux d'affectation", f"{s['assignment_rate']*100:.1f} %",
              help=f"{s['n_assigned']} paires (élève, demande) affectées sur {s['n_expected']}")


def not_assigned(state):
    df = state.report.not_assigned()
    if df.empty:
        st.success("Toutes les paires (élève, demande) attendues ont été affectées.")
        return
    st.caption(f"{len(df)} paires non affectées — la colonne « Cause » détaille "
               "la ventilation des vœux (saturés, non accessibles, etc.).")
    st.dataframe(df, column_config=L.NOT_ASSIGNED, use_container_width=True, hide_index=True)


def filling(state):
    df = _translate_period(state.report.filling())
    st.caption("Une ligne par occurrence. Cliquez sur une ligne pour voir les "
               "étudiants admis. Rouge = dépassement effectif max. Jaune = sous l'effectif min.")
    def _style(row):
        if row["over_max"]: return ["background-color: #fecaca"] * len(row)
        if row["under_min"]: return ["background-color: #fef3c7"] * len(row)
        return [""] * len(row)
    sel = st.dataframe(df.style.apply(_style, axis=1), column_config=L.FILLING,
                       use_container_width=True, hide_index=True,
                       on_select="rerun", selection_mode="single-row")
    if sel and sel.selection.rows:
        _show_enrolled(state, df.iloc[sel.selection.rows[0]]["id_occ"])


def _show_enrolled(state, id_occ):
    o = state.campaign.occurrences[id_occ]
    st.markdown(f"##### Étudiants admis dans `{o.code_ue}` — {o.label}")
    def row(sid, did):
        s = state.campaign.students.get(sid); v = state.campaign.voeu_of(sid, did)
        return {"Élève": sid, "Régime": L.REGIME_LABEL.get(s.regime, s.regime) if s else "",
                "Francophone": "OUI" if s and s.francophone else "NON",
                "Filière(s)": "+".join(s.filieres) if s else "",
                "Rang obtenu": f"#{rank(v, id_occ)}" if v else "n/a"}
    rows = [row(sid, did) for (sid, did), oid in state.assignment.items() if oid == id_occ]
    if not rows: st.write("Aucun étudiant affecté à cette occurrence."); return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def per_demande(state):
    st.caption("Répartition complète des rangs pour chaque demande. Choisissez "
               "le mode d'affichage puis dépliez chaque bloc.")
    mode = st.radio("Vue", ["Histogramme", "Tableau horizontal"], horizontal=True,
                    label_visibility="collapsed")
    par_d = state.report.ranks_per_demande()
    for id_demande in state.campaign.demandes():
        rs = par_d.get(id_demande, [])
        dist = dict(Counter(rs))
        title = (f"Demande {id_demande} — {len(rs)} affectations — "
                 f"rang moyen {sum(rs)/len(rs):.2f} — pire rang #{max(rs)}"
                 if rs else f"Demande {id_demande} — aucune affectation")
        with st.expander(title):
            if not dist: st.info("Aucune affectation dans cette demande."); continue
            (rank_histogram if mode == "Histogramme" else rank_kpi_row)(dist)


def compensation(state):
    st.caption("Vue par élève. Tri décroissant sur « Pire rang » pour détecter "
               "les élèves systématiquement mal servis.")
    st.dataframe(
        state.report.stats_compensation().sort_values("worst_rank", ascending=False),
        column_config=L.STATS_COMP, use_container_width=True, hide_index=True)


def export(state):
    from .export_view import render
    render(state)
