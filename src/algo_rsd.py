"""Random Serial Dictator (§13.6). Baseline très simple, robuste à la déclaration."""
from __future__ import annotations
import random
from .model import Instance, Assignment
from .common import couts_accessibles, empty_assignment

NAME = "rsd"


def solve(inst: Instance, seed: int = 0) -> Assignment:
    rng = random.Random(seed)
    order = list(inst.students)
    rng.shuffle(order)
    reste = {o.id_occ: o.cap_dispo for o in inst.occurrences}
    result = empty_assignment(inst)

    for s in order:
        for bloc in inst.blocs:
            for o, _cost in couts_accessibles(inst, s, bloc):
                if reste[o.id_occ] > 0:
                    result[s.id_eleve][bloc] = o.id_occ
                    reste[o.id_occ] -= 1
                    break
    return result
