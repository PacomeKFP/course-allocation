"""Modèle de données — dataclasses pures, aucune logique métier.

Nomenclature Synapse :
  * ``Voeu`` = liste d'``id_occ`` classés pour un couple (élève, demande).
  * ``Campaign`` = agrégat élèves + occurrences + vœux d'une campagne.
  * ``Assignment`` = dict {(id_student, id_demande) → id_occ | None}.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Student:
    id_student: str            # PersID (identifiant Synapse)
    id_dossier: str            # IDDossierEtudiant
    regime: str                # "student" | "apprentice" | "auditor"
    francophone: bool
    filieres: list[str]        # codes bruts Synapse (DSAI, MACS, ...)


@dataclass
class Occurrence:
    id_occ: str                # Idoccur (unique)
    id_ue: str                 # Idue (groupe de la même UE)
    code_ue: str               # Codeue (ex : APM_4TC01_TP) — pour affichage
    label: str                 # Intituleoccur
    period: int                # 1..4
    slot: str                  # ex : "Me-am", ou "" si non fixé
    language: str              # "FR" | "EN"
    fisea: bool                # réservée aux apprentis
    cap_max: int
    cap_min: int = 0
    already_enrolled: int = 0

    @property
    def cap_available(self) -> int:
        return max(0, self.cap_max - self.already_enrolled)


@dataclass
class Voeu:
    id_student: str
    id_demande: str            # IDDemande (identifiant Synapse)
    id_campagne: str
    ranked_occurrences: list[str]  # id_occ ordonnés du + préféré au - préféré


@dataclass
class Campaign:
    id_campagne: str
    students: dict[str, Student] = field(default_factory=dict)
    occurrences: dict[str, Occurrence] = field(default_factory=dict)
    voeux: list[Voeu] = field(default_factory=list)  # non-vides uniquement

    def demandes(self) -> list[str]:
        return sorted({v.id_demande for v in self.voeux})

    def voeu_of(self, id_student: str, id_demande: str) -> Voeu | None:
        return next((v for v in self.voeux
                     if v.id_student == id_student and v.id_demande == id_demande), None)


# Une assignation : (id_student, id_demande) -> id_occ ou None si non affecté.
Assignment = dict[tuple[str, str], str | None]
