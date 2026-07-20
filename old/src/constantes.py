"""Constantes du système — source unique de vérité.

Tout ce qui vient des CSV mais reste stable dans le temps (mapping
filière→groupe, table des créneaux par groupe, jours ouvrés) est regroupé
ici. Ainsi un changement côté scolarité ne touche qu'un seul fichier.
"""
from __future__ import annotations

# Mapping filière (code Synapse) → groupe de créneau (A/B/C).
# Source : data/2026/Liste des filières avec créneaux 2026-2027.csv
FILIERE_TO_GROUPE: dict[str, str] = {
    # Groupe A
    "CYBER": "A", "GIN": "A", "IGR": "A", "MACS": "A", "SLR": "A", "TELECOM": "A",
    # Groupe B
    "IMA": "B", "MITRO": "B", "MODS": "B", "SE": "B",
    # Groupe C
    "ACCQ": "C", "DSAI": "C", "RIO": "C", "SPAI": "C",
}

# Filières présentes chez les élèves mais sans créneau documenté.
# Elles n'imposent aucune contrainte horaire (cf. cahier §12).
FILIERES_SANS_CRENEAU: set[str] = {"TSIA", "SD", "ENTP", "RECH"}

CRENEAUX = ["Lu-am", "Lu-pm", "Ma-am", "Ma-pm", "Me-am", "Me-pm", "Ve-am", "Ve-pm"]
CRENEAUX_UNIVERSELS = ["Ma-pm", "Me-am"]     # libres pour tous les élèves
JOURS = ["Lundi", "Mardi", "Mercredi", "Vendredi"]  # le jeudi n'accueille pas de TC

# Créneaux occupés par chaque groupe de filière à chaque période (§6.2).
CRENEAUX_GROUPES: dict[str, dict[int, list[str]]] = {
    "A": {1: ["Lu-am", "Me-pm"], 2: ["Lu-am", "Me-pm"],
          3: ["Lu-pm", "Ve-am"], 4: ["Lu-pm", "Ve-am"]},
    "B": {1: ["Lu-pm", "Ve-am"], 2: ["Lu-pm", "Ve-am"],
          3: ["Lu-am", "Me-pm"], 4: ["Lu-am", "Me-pm"]},
    "C": {p: ["Ma-am", "Ve-pm"] for p in (1, 2, 3, 4)},
}

# Passage créneau → jour (le préfixe suffit).
JOUR_DU_CRENEAU: dict[str, str] = {
    "Lu-am": "Lundi", "Lu-pm": "Lundi",
    "Ma-am": "Mardi", "Ma-pm": "Mardi",
    "Me-am": "Mercredi", "Me-pm": "Mercredi",
    "Ve-am": "Vendredi", "Ve-pm": "Vendredi",
}

# Bonus retranché au coût quand un anglophone reçoit un cours en anglais.
BONUS_ANGLOPHONE = 2

# Pénalité prohibitive pour les slacks « non-affecté » et autres violations
# souples encodées dans les objectifs MIP (algo_mip, algo_mip_full).
BIG_M = 10_000

# Charge institutionnelle : 1 bloc = 1 période occupée = 2,5 crédits.
CREDITS_PAR_BLOC = 2.5
CIBLE_FISE = 15.0        # ≥ 6 blocs pour un étudiant classique
CIBLE_FISEA = 7.5        # ≥ 3 ECUE (× 2 semestres / 2) pour un apprenti


def jours_ecole_apprenti(groupe: str, periode: int) -> set[str]:
    """Jours où l'apprenti a cours (une filière → 2 créneaux → 1 ou 2 jours)."""
    return {JOUR_DU_CRENEAU[c] for c in CRENEAUX_GROUPES[groupe][periode]}


def jours_entreprise_apprenti(groupe: str, periode: int) -> set[str]:
    """Jours d'entreprise de l'apprenti pour cette période (§7, note N7).

    Sur les 4 jours de tronc commun (lu, ma, me, ve), 2 sont pris par les cours
    de filière → école, les 2 autres → entreprise (bloqués). Le jeudi est
    chômé et n'entre pas dans le calcul.
    """
    return set(JOURS) - jours_ecole_apprenti(groupe, periode)


def semestre_de_periode(periode: int) -> int:
    return 1 if periode in (1, 2) else 2


def export_mappings_csv(path: str) -> None:
    """Ré-exporte le mapping filière→groupe pour audit humain."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["code_filiere", "groupe"])
        for code, g in sorted(FILIERE_TO_GROUPE.items()):
            w.writerow([code, g])
        for code in sorted(FILIERES_SANS_CRENEAU):
            w.writerow([code, ""])
