"""Libellés français + aides + formats pour les tableaux Streamlit.

Regroupe ici tout ce qui touche à l'affichage : traductions des noms
techniques (id_student → « Élève »), colonnes formatées (période
académique S1-P1…), textes d'aide (tooltips) pour rendre l'IHM
compréhensible à un non-spécialiste.
"""
from __future__ import annotations
import streamlit as st

PERIOD_LABEL = {0: "?", 1: "S1-P1", 2: "S1-P2", 3: "S2-P3", 4: "S2-P4"}
REGIME_LABEL = {"student": "Étudiant", "apprentice": "Apprenti",
                "auditor": "Auditeur libre"}


def fmt_period(p) -> str:
    return PERIOD_LABEL.get(int(p), str(p)) if p not in (None, "") else ""


def cfg(**kwargs):
    """Raccourci vers ``st.column_config.Column``."""
    return st.column_config.Column(**kwargs)


NOT_ASSIGNED = {
    "id_student": cfg(label="Élève", help="Identifiant Synapse de l'étudiant"),
    "id_demande": cfg(label="Demande", help="Identifiant Synapse de la demande (~bloc)"),
    "regime": cfg(label="Régime"),
    "filieres": cfg(label="Filière(s)"),
    "n_voeux": st.column_config.NumberColumn(
        label="Nb vœux", help="Nombre d'occurrences classées par l'élève pour cette demande"),
    "cause": cfg(label="Cause probable",
                 help="Raison diagnostique de la non-affectation"),
}

FILLING = {
    "id_occ": cfg(label="ID occ.", help="Identifiant Synapse de l'occurrence"),
    "code_ue": cfg(label="Code UE"),
    "label": cfg(label="Intitulé"),
    "period": cfg(label="Période", help="S1-P1, S1-P2, S2-P3 ou S2-P4"),
    "slot": cfg(label="Créneau", help="Lu-am, Ma-pm, etc."),
    "language": cfg(label="Langue"),
    "fisea": st.column_config.CheckboxColumn(
        label="FISEA", help="Réservé aux apprentis"),
    "cap_min": st.column_config.NumberColumn(
        label="Effectif min", help="En-dessous, l'occurrence risque d'être annulée"),
    "cap_max": st.column_config.NumberColumn(label="Effectif max"),
    "n_enrolled": st.column_config.NumberColumn(
        label="Effectif atteint", help="Nombre d'étudiants affectés + déjà inscrits"),
    "under_min": st.column_config.CheckboxColumn(label="< min"),
    "over_max": st.column_config.CheckboxColumn(label="> max"),
}

STATS_DEMANDE = {
    "id_demande": cfg(label="Demande"),
    "n": st.column_config.NumberColumn(
        label="Affectés", help="Nombre d'étudiants ayant obtenu une occurrence dans cette demande"),
    "first_choice": st.column_config.NumberColumn(
        label="1er choix", help="Nombre d'étudiants ayant reçu leur vœu n°1"),
    "avg_rank": st.column_config.NumberColumn(
        label="Rang moyen", format="%.2f",
        help="Moyenne des rangs obtenus (1 = meilleur)"),
    "worst_rank": st.column_config.NumberColumn(
        label="Pire rang", help="Le rang le plus mauvais servi dans cette demande"),
}

STATS_COMP = {
    "id_student": cfg(label="Élève"),
    "n_assigned": st.column_config.NumberColumn(label="Nb affectations"),
    "avg_rank": st.column_config.NumberColumn(label="Rang moyen", format="%.2f"),
    "worst_rank": st.column_config.NumberColumn(
        label="Pire rang", help="Signale les élèves les plus mal servis"),
    "sum_ranks": st.column_config.NumberColumn(
        label="Somme rangs", help="Utile pour comparer la « chance » globale d'un élève"),
}
