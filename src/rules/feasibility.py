"""Faisabilité par paire (élève, occurrence).

Chaque méthode renvoie ``None`` si la règle est respectée, sinon une
chaîne courte donnant la raison du rejet. ``check`` accumule toutes les
raisons pour une paire donnée — pour explicabilité dans le rapport.
"""
from __future__ import annotations
from ..data.model import Student, Occurrence
from ..data.constants import (
    FILIERE_TO_GROUPE, SLOTS_BY_GROUP, DAY_OF_SLOT, company_days,
)


class Feasibility:
    """Règles élémentaires d'accessibilité (élève, occurrence)."""

    def slot_defined(self, s: Student, o: Occurrence) -> str | None:
        if not o.slot:
            return "créneau non fixé pour cette occurrence"
        return None

    def fisea_ok(self, s: Student, o: Occurrence) -> str | None:
        if o.fisea and s.regime != "apprentice":
            return "occurrence FISEA réservée aux apprentis"
        return None

    def slot_free(self, s: Student, o: Occurrence) -> str | None:
        """Le créneau doit être libre au sens des filières de l'élève."""
        for f in s.filieres:
            g = FILIERE_TO_GROUPE.get(f)
            if g and o.slot in SLOTS_BY_GROUP[g][o.period]:
                return f"créneau {o.slot} occupé par filière {f}"
        return None

    def company_day(self, s: Student, o: Occurrence) -> str | None:
        """Un apprenti ne peut pas suivre un cours un jour d'entreprise."""
        if s.regime != "apprentice" or not s.filieres:
            return None
        g = FILIERE_TO_GROUPE.get(s.filieres[0])
        if g and DAY_OF_SLOT[o.slot] in company_days(g, o.period):
            return f"jour {DAY_OF_SLOT[o.slot]} en entreprise"
        return None

    def language(self, s: Student, o: Occurrence) -> str | None:
        """Anglophone → cours en anglais uniquement (S1 ET S2)."""
        if not s.francophone and o.language == "FR":
            return "cours en français, élève anglophone"
        return None

    def check(self, s: Student, o: Occurrence) -> list[str]:
        """Toutes les raisons d'exclusion pour ce couple ; vide = accessible."""
        return [msg for msg in (
            self.slot_defined(s, o), self.fisea_ok(s, o), self.slot_free(s, o),
            self.company_day(s, o), self.language(s, o),
        ) if msg]

    def is_accessible(self, s: Student, o: Occurrence) -> bool:
        return not self.check(s, o)
