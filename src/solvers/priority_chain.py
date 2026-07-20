"""Étape 1 du pipeline : pré-affectations prioritaires.

Chaque méthode ``priorité_XXX`` traite une catégorie protégée et
enregistre les affectations partielles avant l'optimisation. Pour
ajouter une priorité : écrire une méthode et l'ajouter à ``self.rules``.
"""
from __future__ import annotations
from ..data.model import Campaign, Assignment
from ..rules import Feasibility
from .base import empty_assignment, rank


class PriorityChain:
    """Applique les priorités métier avant l'optimisation générale."""

    def __init__(self, feasibility: Feasibility | None = None):
        self.feasibility = feasibility or Feasibility()
        self.rules = [self.anglophones_to_english, self.apprentices_to_fisea]

    def apply(self, campaign: Campaign) -> Assignment:
        """Exécute toutes les priorités et renvoie l'assignation partielle."""
        assignment = empty_assignment(campaign)
        remaining = {oid: o.cap_available for oid, o in campaign.occurrences.items()}
        for rule in self.rules:
            rule(campaign, assignment, remaining)
        return assignment

    def anglophones_to_english(self, campaign, assignment, remaining) -> None:
        """Sert d'abord les anglophones sur les occurrences en anglais."""
        for v in campaign.voeux:
            if assignment[(v.id_student, v.id_demande)] is not None:
                continue
            s = campaign.students[v.id_student]
            if s.francophone:
                continue
            self._assign_best(v, campaign, assignment, remaining,
                              filt=lambda o: o.language == "EN")

    def apprentices_to_fisea(self, campaign, assignment, remaining) -> None:
        """Sert d'abord les apprentis sur les occurrences FISEA."""
        for v in campaign.voeux:
            if assignment[(v.id_student, v.id_demande)] is not None:
                continue
            s = campaign.students[v.id_student]
            if s.regime != "apprentice":
                continue
            self._assign_best(v, campaign, assignment, remaining,
                              filt=lambda o: o.fisea)

    def _assign_best(self, v, campaign, assignment, remaining, filt) -> None:
        """Meilleur choix accessible, respectant ``filt`` et la capacité."""
        s = campaign.students[v.id_student]
        for id_occ in v.ranked_occurrences:
            o = campaign.occurrences.get(id_occ)
            if not o or not filt(o) or remaining.get(id_occ, 0) == 0:
                continue
            if self.feasibility.is_accessible(s, o):
                assignment[(v.id_student, v.id_demande)] = id_occ
                remaining[id_occ] -= 1
                return
