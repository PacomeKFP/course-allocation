"""Constantes métier stables — source unique de vérité.

Toute donnée invariante d'année en année vit ici : mapping filière→groupe,
créneaux réservés par chaque groupe, jours ouvrés, poids par défaut de la
fonction de coût. Un changement scolarité ne touche qu'un fichier.
"""
from __future__ import annotations

# Filière (code Synapse) → groupe de créneau (A/B/C).
FILIERE_TO_GROUPE: dict[str, str] = {
    "CYBER": "A", "GIN": "A", "IGR": "A", "MACS": "A", "SLR": "A", "TELECOM": "A",
    "IMA": "B", "MITRO": "B", "MODS": "B", "SE": "B",
    "ACCQ": "C", "DSAI": "C", "RIO": "C", "SPAI": "C",
}

# Filières sans mapping (aucune contrainte horaire imposée par la filière).
FILIERES_SANS_CRENEAU: set[str] = {"TSIA", "SD", "ENTP", "RECH"}

SLOTS = ["Lu-am", "Lu-pm", "Ma-am", "Ma-pm", "Me-am", "Me-pm", "Ve-am", "Ve-pm"]
DAYS = ["Lundi", "Mardi", "Mercredi", "Vendredi"]  # jeudi non utilisé

# Créneaux occupés par chaque groupe à chaque période (§6.2 du cahier).
SLOTS_BY_GROUP: dict[str, dict[int, list[str]]] = {
    "A": {1: ["Lu-am", "Me-pm"], 2: ["Lu-am", "Me-pm"],
          3: ["Lu-pm", "Ve-am"], 4: ["Lu-pm", "Ve-am"]},
    "B": {1: ["Lu-pm", "Ve-am"], 2: ["Lu-pm", "Ve-am"],
          3: ["Lu-am", "Me-pm"], 4: ["Lu-am", "Me-pm"]},
    "C": {p: ["Ma-am", "Ve-pm"] for p in (1, 2, 3, 4)},
}

DAY_OF_SLOT: dict[str, str] = {
    "Lu-am": "Lundi", "Lu-pm": "Lundi",
    "Ma-am": "Mardi", "Ma-pm": "Mardi",
    "Me-am": "Mercredi", "Me-pm": "Mercredi",
    "Ve-am": "Vendredi", "Ve-pm": "Vendredi",
}

# Défauts pour la fonction de coût (surchargeable dans MipSolver).
COST_POWER = 2                  # rang^2 — pénalité quadratique
ENGLISH_MATCH_BONUS = 2         # rabais anglophone → cours EN
BIG_M = 10_000                  # pénalité prohibitive pour slack


def semester_of(period: int) -> int:
    return 1 if period in (1, 2) else 2


def company_days(group: str, period: int) -> set[str]:
    """Jours d'entreprise d'un apprenti (les 2 jours hors filière, hors jeudi)."""
    school_days = {DAY_OF_SLOT[s] for s in SLOTS_BY_GROUP[group][period]}
    return set(DAYS) - school_days
