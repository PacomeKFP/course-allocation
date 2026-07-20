"""Deferred Acceptance / Gale-Shapley côté élève (§13.4).

Utilise ``matching.games.HospitalResident``. Résolution bloc par bloc (la lib
gère un unique appariement à la fois).

Priorité des occurrences : anglophones d'abord sur les cours en anglais, sinon
ordre déterministe stable.
"""
from __future__ import annotations
import random
from matching.games import HospitalResident
from .model import Instance, Assignment
from .common import couts_accessibles, empty_assignment
from .filters import accessible

NAME = "da"


def solve(inst: Instance, seed: int = 0) -> Assignment:
    rng = random.Random(seed)
    result = empty_assignment(inst)
    for bloc in inst.blocs:
        _solve_bloc(inst, bloc, result, rng)
    return result


def _priority_key(s, o):
    """Plus petit = prioritaire pour l'occurrence."""
    anglo_prio = 0 if (s.langue == "EN" and o.langue == "EN") else 1
    return (anglo_prio, s.id_eleve)


def _solve_bloc(inst: Instance, bloc: str, result: Assignment, rng: random.Random) -> None:
    occs = [o for o in inst.occ_by_bloc(bloc) if o.cap_dispo > 0]
    if not occs:
        return

    resident_prefs: dict[str, list[str]] = {}
    for s in inst.students:
        ranked = [o for o, _ in couts_accessibles(inst, s, bloc)]
        if ranked:
            resident_prefs[s.id_eleve] = [o.id_occ for o in ranked]

    hospital_prefs: dict[str, list[str]] = {}
    hospital_caps: dict[str, int] = {}
    for o in occs:
        acceptables = [s for s in inst.students if accessible(s, o)]
        acceptables.sort(key=lambda s: _priority_key(s, o))
        hospital_prefs[o.id_occ] = [s.id_eleve for s in acceptables]
        hospital_caps[o.id_occ] = o.cap_dispo

    # HospitalResident exige la mutualité stricte des listes de préférences.
    for sid, hs in list(resident_prefs.items()):
        resident_prefs[sid] = [h for h in hs if sid in hospital_prefs.get(h, [])]
        if not resident_prefs[sid]:
            del resident_prefs[sid]
    for hid, rs in list(hospital_prefs.items()):
        hospital_prefs[hid] = [r for r in rs if hid in resident_prefs.get(r, [])]

    game = HospitalResident.create_from_dictionaries(
        resident_prefs, hospital_prefs, hospital_caps)
    matched = game.solve(optimal="resident")
    for h, residents in matched.items():
        for r in residents:
            result[str(r)][bloc] = str(h)
