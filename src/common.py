"""Helpers partagés par tous les algorithmes."""
from __future__ import annotations
from .model import Instance, Student, Occurrence, Assignment
from .constantes import BONUS_ANGLOPHONE
from .filters import occ_accessibles


def rang(s: Student, o: Occurrence) -> int:
    """0-based rang de l'UE dans les vœux du bloc, ou ``len(wishes)`` si non classé."""
    wishes = s.voeux_par_bloc.get(o.bloc, [])
    try:
        return wishes.index(o.id_ue)
    except ValueError:
        return len(wishes)


def cout(s: Student, o: Occurrence) -> int:
    """Coût d'affecter ``s`` à ``o`` (plus bas = meilleur).

    Rang + pénalité si non classé + bonus anglophone → cours en anglais.
    """
    wishes = s.voeux_par_bloc.get(o.bloc, [])
    r = wishes.index(o.id_ue) if o.id_ue in wishes else len(wishes) + 5
    if s.langue == "EN" and o.langue == "EN":
        r -= BONUS_ANGLOPHONE
    return r


def couts_accessibles(inst: Instance, s: Student, bloc: str) -> list[tuple[Occurrence, int]]:
    """Liste (occurrence, coût) accessibles à ``s`` sur ``bloc``, triée par coût."""
    accs = occ_accessibles(inst, s, bloc)
    scored = [(o, cout(s, o)) for o in accs]
    scored.sort(key=lambda x: x[1])
    return scored


def empty_assignment(inst: Instance) -> Assignment:
    return {s.id_eleve: {b: None for b in inst.blocs} for s in inst.students}


def reste_capacite(inst: Instance, a: Assignment) -> dict[str, int]:
    """Places restantes par occurrence après application de l'affectation ``a``."""
    used = {o.id_occ: 0 for o in inst.occurrences}
    for eid in a:
        for oid in a[eid].values():
            if oid:
                used[oid] += 1
    return {o.id_occ: o.cap_dispo - used[o.id_occ] for o in inst.occurrences}


def group_by(items, key_fn) -> dict:
    """Regroupe ``items`` en dict ``{clé: [items…]}`` selon ``key_fn``."""
    groups: dict = {}
    for it in items:
        groups.setdefault(key_fn(it), []).append(it)
    return groups
