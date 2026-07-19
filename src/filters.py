"""Accessibilité d'une occurrence pour un élève (§7 du cahier).

Une occurrence est accessible si tous les filtres passent :
  1. son créneau n'est pas occupé par une filière de l'élève ;
  2. son jour n'est pas un jour d'entreprise (pour un apprenti, calculé
     dynamiquement à partir de sa filière et de la période, cf. constantes) ;
  3. la langue est compatible (règle §7 point 3, uniquement en S1) ;
  4. FISEA ⇒ élève apprenti.

``raison_rejet`` sert au reporting (exposition explicite de la cause).
"""
from __future__ import annotations
from .model import Instance, Occurrence, Student
from .constantes import (CRENEAUX_GROUPES, JOUR_DU_CRENEAU,
                         jours_entreprise_apprenti)


def creneaux_occupes(s: Student, periode: int) -> set[str]:
    """Union des créneaux réservés par les filières de l'élève à cette période."""
    out: set[str] = set()
    for g in s.groupes_filiere:
        out.update(CRENEAUX_GROUPES[g][periode])
    return out


def jour_bloque(s: Student, periode: int) -> set[str]:
    """Jours où l'élève ne peut pas avoir cours (entreprise pour apprentis)."""
    if s.regime == "apprenti" and s.groupes_filiere:
        return jours_entreprise_apprenti(s.groupes_filiere[0], periode)
    return set()


def raison_rejet(s: Student, o: Occurrence) -> str | None:
    """``None`` si accessible, sinon une chaîne explicative."""
    if not o.creneau:
        return "créneau non fixé pour cette occurrence"
    if o.fisea and s.regime != "apprenti":
        return "occurrence FISEA (réservée aux apprentis)"
    if o.creneau in creneaux_occupes(s, o.periode):
        return f"créneau {o.creneau} occupé par filière {s.groupes_filiere}"
    jour = JOUR_DU_CRENEAU[o.creneau]
    if jour in jour_bloque(s, o.periode):
        return f"jour {jour} en entreprise (apprenti)"
    if s.langue == "EN" and o.periode in (1, 2) and o.langue == "FR":
        return "cours en français, élève anglophone (S1)"
    return None


def accessible(s: Student, o: Occurrence) -> bool:
    return raison_rejet(s, o) is None


def occ_accessibles(inst: Instance, s: Student, bloc: str) -> list[Occurrence]:
    return [o for o in inst.occ_by_bloc(bloc) if accessible(s, o)]
