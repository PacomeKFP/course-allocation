"""Accessibilité d'une occurrence pour un élève (§7 du cahier).

Une occurrence est accessible à un élève si tous les filtres passent :
  1. son créneau n'est occupé par aucune filière de l'élève ;
  2. son jour n'est pas bloqué (pour un apprenti) ;
  3. la langue est compatible (règle §7 point 3, uniquement en S1) ;
  4. FISEA ⇒ élève apprenti ; FISEA=False + apprenti est accepté par défaut.

On expose une fonction principale ``accessible`` + un helper qui renvoie la
raison précise d'un rejet, utilisé par le reporting.
"""
from __future__ import annotations
from .model import Instance, Occurrence, Student, CRENEAUX_GROUPES

_JOUR_DU_CRENEAU = {"Lu-am": "Lundi", "Lu-pm": "Lundi",
                    "Ma-am": "Mardi", "Ma-pm": "Mardi",
                    "Me-am": "Mercredi", "Me-pm": "Mercredi",
                    "Ve-am": "Vendredi", "Ve-pm": "Vendredi"}


def creneaux_occupes(s: Student, periode: int) -> set[str]:
    """Union des créneaux réservés par les filières de l'élève à cette période."""
    out: set[str] = set()
    for g in s.groupes_filiere:
        out.update(CRENEAUX_GROUPES[g][periode])
    return out


def raison_rejet(s: Student, o: Occurrence) -> str | None:
    """Renvoie ``None`` si accessible, sinon une chaîne explicative."""
    if not o.creneau:
        return "créneau non fixé pour cette occurrence"
    if o.fisea and s.regime != "apprenti":
        return "occurrence FISEA (réservée aux apprentis)"
    if o.creneau in creneaux_occupes(s, o.periode):
        return f"créneau {o.creneau} occupé par filière {s.groupes_filiere}"
    jour = _JOUR_DU_CRENEAU[o.creneau]
    if jour in s.jours_bloques:
        return f"jour {jour} bloqué (apprenti)"
    # Langue : anglophone en S1 uniquement.
    if s.langue == "EN" and o.periode in (1, 2) and o.langue == "FR":
        return "cours en français, élève anglophone (S1)"
    return None


def accessible(s: Student, o: Occurrence) -> bool:
    return raison_rejet(s, o) is None


def occ_accessibles(inst: Instance, s: Student, bloc: str) -> list[Occurrence]:
    return [o for o in inst.occ_by_bloc(bloc) if accessible(s, o)]
