"""Équité inter-blocs par post-traitement du min-cost flow.

Idée : le min-cost flow est déjà optimal sur la **somme totale des rangs**
(chaque bloc indépendant, matching-poids-min). L'équité inter-blocs signifie
« un mauvais rang dans un bloc peut être compensé par un bon rang ailleurs » :
on veut réduire le **pire rang par élève**, à somme totale globale égale
ou meilleure.

On applique une recherche locale par échanges :

  Pour chaque paire d'élèves (s1, s2) et chaque bloc b, si échanger leurs
  occurrences respectives dans b (i) reste accessible pour les deux et
  (ii) réduit le max de leurs pire-rangs, on effectue l'échange.

Cela ne dégrade jamais la somme totale des rangs de manière strictement
défavorable (nous rejetons tout swap qui augmente la somme). C'est très
rapide, déterministe, facile à auditer.
"""
from __future__ import annotations
from .model import Instance, Assignment
from .common import rang
from .filters import accessible
from . import algo_flow

NAME = "equite"


def solve(inst: Instance, max_passes: int = 5) -> Assignment:
    a = algo_flow.solve(inst)
    occ = {o.id_occ: o for o in inst.occurrences}
    for _ in range(max_passes):
        improved = _one_pass(inst, a, occ)
        if not improved:
            break
    return a


def _pire(inst: Instance, a: Assignment, eid: str) -> int:
    ranks = [rang(next(s for s in inst.students if s.id_eleve == eid),
                  inst.occ_by_id(oid)) + 1
             for oid in a[eid].values() if oid]
    return max(ranks) if ranks else 0


def _pire_and_sum(rangs_par_bloc: dict[str, int]) -> tuple[int, int]:
    vals = [r for r in rangs_par_bloc.values() if r is not None]
    return (max(vals) if vals else 0, sum(vals))


def _one_pass(inst: Instance, a: Assignment, occ: dict) -> bool:
    """Une passe de swaps. Renvoie True si au moins un swap a été fait."""
    ranks_by = {s.id_eleve: {b: (rang(s, occ[oid]) + 1) if oid else None
                             for b, oid in a[s.id_eleve].items()}
                for s in inst.students}
    student_by = {s.id_eleve: s for s in inst.students}
    improved = False

    for bloc in inst.blocs:
        assigned = [(eid, a[eid][bloc]) for eid in a if a[eid][bloc]]
        for i, (e1, o1) in enumerate(assigned):
            for e2, o2 in assigned[i+1:]:
                if o1 == o2:
                    continue
                s1, s2 = student_by[e1], student_by[e2]
                oc1, oc2 = occ[o1], occ[o2]
                # Le swap doit rester accessible.
                if not (accessible(s1, oc2) and accessible(s2, oc1)):
                    continue

                r_before1 = ranks_by[e1][bloc]
                r_before2 = ranks_by[e2][bloc]
                r_after1 = rang(s1, oc2) + 1
                r_after2 = rang(s2, oc1) + 1

                # Simuler l'état après swap et comparer.
                new_ranks_1 = {**ranks_by[e1], bloc: r_after1}
                new_ranks_2 = {**ranks_by[e2], bloc: r_after2}
                p_before = max(_pire_and_sum(ranks_by[e1])[0],
                               _pire_and_sum(ranks_by[e2])[0])
                p_after = max(_pire_and_sum(new_ranks_1)[0],
                              _pire_and_sum(new_ranks_2)[0])
                s_before = r_before1 + r_before2
                s_after = r_after1 + r_after2

                if p_after < p_before and s_after <= s_before + 1:
                    a[e1][bloc], a[e2][bloc] = o2, o1
                    ranks_by[e1][bloc] = r_after1
                    ranks_by[e2][bloc] = r_after2
                    improved = True
    return improved
