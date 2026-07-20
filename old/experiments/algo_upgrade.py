"""Approche 1 : allocation initiale gloutonne + upgrade itératif.

Idée utilisateur (résumée) :
  1. Placer tout le monde quelque part d'abord (allocation faisable).
  2. Itérer : chaque élève tente d'améliorer son pire rang par swap ou
     par déplacement vers une occurrence moins pleine et mieux notée.
  3. Convergence lorsque plus aucun swap améliorant n'est possible.

Différence avec :class:`src.algo_equite` : ici on part d'une allocation
aléatoire (pas de flow d'optimum garanti), et on relâche la contrainte
« somme des rangs préservée » pour explorer plus large.
"""
from __future__ import annotations
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.model import Instance, Assignment
from src.common import empty_assignment, rang, reste_capacite
from src.filters import accessible, occ_accessibles

NAME = "upgrade"


def solve(inst: Instance, seed: int = 0, max_passes: int = 30) -> Assignment:
    a = _initial(inst, seed)
    for i in range(max_passes):
        if not _swap_pass(inst, a, seed + i):
            break
    return a


def _initial(inst: Instance, seed: int) -> Assignment:
    """Placement initial : ordre aléatoire, chacun prend son meilleur vœu libre."""
    rng = random.Random(seed)
    order = sorted(inst.students, key=lambda _: rng.random())
    reste = {o.id_occ: o.cap_dispo for o in inst.occurrences}
    result = empty_assignment(inst)
    for s in order:
        for bloc in inst.blocs:
            if not s.voeux_par_bloc.get(bloc):
                continue
            for o in sorted(occ_accessibles(inst, s, bloc), key=lambda o: rang(s, o)):
                if reste[o.id_occ] > 0:
                    result[s.id_eleve][bloc] = o.id_occ
                    reste[o.id_occ] -= 1
                    break
    return result


def _swap_pass(inst: Instance, a: Assignment, seed: int) -> bool:
    """Une passe : swap entre paires d'élèves si le max de leurs rangs baisse."""
    rng = random.Random(seed)
    occ = {o.id_occ: o for o in inst.occurrences}
    student = {s.id_eleve: s for s in inst.students}
    reste = reste_capacite(inst, a)
    improved = False

    for bloc in inst.blocs:
        assigned = [(eid, a[eid][bloc]) for eid in a if a[eid][bloc]]
        rng.shuffle(assigned)

        # Tentative 1 : déplacer vers une occurrence libre mieux classée.
        for eid, oid in list(assigned):
            s = student[eid]
            r_now = rang(s, occ[oid]) + 1
            for o in occ_accessibles(inst, s, bloc):
                if o.id_occ == oid or reste[o.id_occ] == 0:
                    continue
                if rang(s, o) + 1 < r_now:
                    reste[oid] += 1
                    reste[o.id_occ] -= 1
                    a[eid][bloc] = o.id_occ
                    improved = True
                    break

        # Tentative 2 : swap entre deux élèves si le max des deux rangs baisse.
        assigned = [(eid, a[eid][bloc]) for eid in a if a[eid][bloc]]
        for i, (e1, o1) in enumerate(assigned):
            for e2, o2 in assigned[i+1:]:
                if o1 == o2:
                    continue
                s1, s2 = student[e1], student[e2]
                if not (accessible(s1, occ[o2]) and accessible(s2, occ[o1])):
                    continue
                r1a, r2a = rang(s1, occ[o1]) + 1, rang(s2, occ[o2]) + 1
                r1b, r2b = rang(s1, occ[o2]) + 1, rang(s2, occ[o1]) + 1
                if max(r1b, r2b) < max(r1a, r2a):
                    a[e1][bloc], a[e2][bloc] = o2, o1
                    improved = True
    return improved


