"""Allocation équitable via ``fairpyx`` (§13.5).

Note : ``fairpyx`` n'expose pas directement A-CEEI/Course-Match ; on utilise à
la place ``iterated_maximum_matching_adjusted``, qui itère des couplages
maximums pondérés avec correction d'équité entre agents. C'est le plus proche
disponible dans la lib, cf. ``docs/notes.md`` N16.

Modélisation :
  * utilité(élève, occurrence) = ``100 − rang`` (plus grand = meilleur),
    bonus anglophone additif ;
  * conflits d'items : dans un même bloc, les occurrences sont mutuellement
    exclusives (l'élève n'en prend qu'une) ;
  * capacité agent = nombre de blocs ; capacité item = places disponibles.
"""
from __future__ import annotations
from fairpyx import Instance as FpxInstance, divide
from fairpyx.algorithms import iterated_maximum_matching_adjusted
from .model import Instance, Assignment
from .constantes import BONUS_ANGLOPHONE
from .common import rang, empty_assignment
from .filters import accessible

NAME = "aceei"
UTIL_MAX = 100


def solve(inst: Instance) -> Assignment:
    valuations: dict[str, dict[str, int]] = {}
    agent_conflicts: dict[str, list[str]] = {}
    for s in inst.students:
        vals, forb = {}, []
        for o in inst.occurrences:
            if accessible(s, o):
                u = max(1, UTIL_MAX - rang(s, o) * 5)
                if s.langue == "EN" and o.langue == "EN":
                    u += BONUS_ANGLOPHONE * 5
                vals[o.id_occ] = u
            else:
                forb.append(o.id_occ)
        valuations[s.id_eleve] = vals
        agent_conflicts[s.id_eleve] = forb

    agent_caps = {s.id_eleve: len(inst.blocs) for s in inst.students}
    item_caps = {o.id_occ: o.cap_dispo for o in inst.occurrences}
    item_conflicts: dict[str, list[str]] = {}
    for b in inst.blocs:
        ids = [o.id_occ for o in inst.occ_by_bloc(b)]
        for oid in ids:
            item_conflicts[oid] = [x for x in ids if x != oid]

    fpx = FpxInstance(valuations=valuations, agent_capacities=agent_caps,
                      item_capacities=item_caps, item_conflicts=item_conflicts,
                      agent_conflicts=agent_conflicts)
    alloc = divide(iterated_maximum_matching_adjusted, instance=fpx)

    result = empty_assignment(inst)
    for eid, items in alloc.items():
        for oid in items:
            bloc = inst.occ_by_id(oid).bloc
            result[eid][bloc] = oid
    return result
