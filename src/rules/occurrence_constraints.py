"""Contraintes entre occurrences — indépendantes de l'élève.

Deux occurrences sont mutuellement exclusives pour tout étudiant si :
  * elles tombent au même instant ``(period, slot)`` — collision d'emploi
    du temps ;
  * elles partagent le même UE — un étudiant ne peut suivre deux fois le
    même ECUE dans l'année.
"""
from __future__ import annotations
from ..data.model import Occurrence
from ..utils import group_by


class OccurrenceConstraints:
    """Émet les paires d'occurrences mutuellement exclusives."""

    def same_instant(self, occurrences: dict[str, Occurrence]) -> list[list[str]]:
        """Groupes d'occurrences au même (période, créneau) : au plus 1 par groupe."""
        buckets = group_by(occurrences.values(), lambda o: (o.period, o.slot))
        return [[o.id_occ for o in occs] for occs in buckets.values() if len(occs) > 1]

    def same_ue(self, occurrences: dict[str, Occurrence]) -> list[list[str]]:
        """Groupes d'occurrences du même UE : au plus 1 par groupe."""
        buckets = group_by(occurrences.values(), lambda o: o.id_ue)
        return [[o.id_occ for o in occs] for occs in buckets.values() if len(occs) > 1]

    def build(self, occurrences: dict[str, Occurrence]) -> list[list[str]]:
        """Toutes les exclusions à imposer, dédupliquées."""
        seen: set[frozenset[str]] = set()
        out: list[list[str]] = []
        for group in self.same_instant(occurrences) + self.same_ue(occurrences):
            key = frozenset(group)
            if key not in seen:
                seen.add(key)
                out.append(sorted(group))
        return out
