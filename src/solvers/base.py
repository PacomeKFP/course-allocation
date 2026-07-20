"""Interface commune des solveurs + helpers de rang et d'assignation."""
from __future__ import annotations
from abc import ABC, abstractmethod
from ..data.model import Campaign, Assignment, Voeu


class Solver(ABC):
    """Toute implémentation d'assignation implémente ``solve(campaign)``."""

    NAME: str = "base"

    @abstractmethod
    def solve(self, campaign: Campaign,
              pre_assignment: Assignment | None = None) -> Assignment:
        """Renvoie une assignation ``(id_student, id_demande) → id_occ | None``."""


def empty_assignment(campaign: Campaign) -> Assignment:
    """Toutes les paires (élève, demande) attendues, initialisées à None."""
    return {(v.id_student, v.id_demande): None for v in campaign.voeux}


def rank(voeu: Voeu, id_occ: str) -> int:
    """Position 1-indexée de ``id_occ`` dans les vœux, ou ``len+1`` si absent."""
    try:
        return voeu.ranked_occurrences.index(id_occ) + 1
    except ValueError:
        return len(voeu.ranked_occurrences) + 1
