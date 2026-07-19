"""Modèle interne unifié — dataclasses simples, sans logique métier.

Voir docs/cahier_des_charges.md §2 pour le vocabulaire.
"""
from __future__ import annotations
from dataclasses import dataclass, field

CRENEAUX = ["Lu-am", "Lu-pm", "Ma-am", "Ma-pm", "Me-am", "Me-pm", "Ve-am", "Ve-pm"]
CRENEAUX_UNIVERSELS = ["Ma-pm", "Me-am"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Vendredi"]

# Créneaux occupés par chaque groupe de filière (§6.2 du cahier).
CRENEAUX_GROUPES: dict[str, dict[int, list[str]]] = {
    "A": {1: ["Lu-am", "Me-pm"], 2: ["Lu-am", "Me-pm"],
          3: ["Lu-pm", "Ve-am"], 4: ["Lu-pm", "Ve-am"]},
    "B": {1: ["Lu-pm", "Ve-am"], 2: ["Lu-pm", "Ve-am"],
          3: ["Lu-am", "Me-pm"], 4: ["Lu-am", "Me-pm"]},
    "C": {p: ["Ma-am", "Ve-pm"] for p in (1, 2, 3, 4)},
}

BONUS_ANGLOPHONE = 2  # rabais soustrait au coût quand anglophone reçoit un cours EN


@dataclass
class Occurrence:
    id_occ: str
    id_ue: str        # code UE (regroupe les occurrences d'une même UE)
    bloc: str
    periode: int      # 1..4
    creneau: str      # dans CRENEAUX, ou "" si non fixé
    langue: str       # "FR" ou "EN"
    fisea: bool       # True → réservée aux apprentis
    cap_max: int
    cap_min: int = 0
    nb_deja_inscrits: int = 0

    @property
    def cap_dispo(self) -> int:
        return max(0, self.cap_max - self.nb_deja_inscrits)


@dataclass
class Student:
    id_eleve: str
    langue: str                # "FR" ou "EN" (francophone = FR)
    regime: str                # "etudiant" | "apprenti" | "auditeur"
    groupes_filiere: list[str] # sous-ensemble de {"A","B","C"}
    jours_bloques: list[str]   # sous-ensemble de JOURS (apprentis seulement)
    voeux_par_bloc: dict[str, list[str]]  # bloc -> liste ordonnée d'id_ue préférés


@dataclass
class Instance:
    students: list[Student]
    occurrences: list[Occurrence]
    blocs: list[str]           # tous les blocs obligatoires

    def occ_by_id(self, id_occ: str) -> Occurrence:
        return next(o for o in self.occurrences if o.id_occ == id_occ)

    def occ_by_bloc(self, bloc: str) -> list[Occurrence]:
        return [o for o in self.occurrences if o.bloc == bloc]

    def ue_to_occs(self, id_ue: str, bloc: str) -> list[Occurrence]:
        return [o for o in self.occurrences if o.id_ue == id_ue and o.bloc == bloc]


# Une affectation : eleveID -> bloc -> id_occ (ou None si non affecté).
Assignment = dict[str, dict[str, str | None]]
