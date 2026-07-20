"""Contraintes entre étudiants et occurrences — dérivées de la faisabilité.

Encode les paires (student, occurrence) interdites, avec la raison, pour
alimentation directe du solveur et traçabilité pour le rapport.
"""
from __future__ import annotations
from ..data.model import Campaign
from .feasibility import Feasibility


class StudentConstraints:
    """Génère la table des paires (élève, occurrence) interdites."""

    def __init__(self, feasibility: Feasibility | None = None):
        self.feasibility = feasibility or Feasibility()

    def build(self, campaign: Campaign) -> dict[tuple[str, str], list[str]]:
        """{(id_student, id_occ) → liste de raisons de rejet}, uniquement les paires interdites."""
        forbidden: dict[tuple[str, str], list[str]] = {}
        for s in campaign.students.values():
            for o in campaign.occurrences.values():
                reasons = self.feasibility.check(s, o)
                if reasons:
                    forbidden[(s.id_student, o.id_occ)] = reasons
        return forbidden

    def allowed_pairs(self, campaign: Campaign) -> set[tuple[str, str]]:
        """Paires (id_student, id_occ) acceptables — utile pour indexer un modèle."""
        forb = self.build(campaign)
        return {(s.id_student, o.id_occ)
                for s in campaign.students.values()
                for o in campaign.occurrences.values()
                if (s.id_student, o.id_occ) not in forb}
