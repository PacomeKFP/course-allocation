"""Modèle interne unifié — dataclasses simples, sans logique métier.

Voir docs/cahier_des_charges.md §2 pour le vocabulaire, et
src/constantes.py pour la table des mappings et les créneaux.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .constantes import (
    CRENEAUX, CRENEAUX_UNIVERSELS, JOURS, CRENEAUX_GROUPES,
    JOUR_DU_CRENEAU, BONUS_ANGLOPHONE, FILIERE_TO_GROUPE, FILIERES_SANS_CRENEAU,
)


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
    intitule: str = ""

    @property
    def cap_dispo(self) -> int:
        return max(0, self.cap_max - self.nb_deja_inscrits)

    @property
    def id_display(self) -> str:
        """Code lisible avec créneau/période : ``APM_4TC01_TP@Me-am/P1``."""
        c = self.creneau or "?"
        return f"{self.id_ue}@{c}/P{self.periode}"


@dataclass
class Student:
    id_eleve: str
    langue: str                # "FR" ou "EN" (francophone = FR)
    regime: str                # "etudiant" | "apprenti" | "auditeur"
    groupes_filiere: list[str] # sous-ensemble de {"A","B","C"}
    voeux_par_bloc: dict[str, list[str]]  # bloc -> liste ordonnée d'id_ue préférés
    # Filières brutes (codes Synapse, avant traduction en groupe A/B/C).
    filieres_brutes: list[str] = field(default_factory=list)


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
