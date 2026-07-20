"""Équité inter-blocs par recherche locale au-dessus du min-cost flow.

Objectif utilisateur : « un mauvais rang dans un bloc doit être compensé
par un bon rang ailleurs » — c'est-à-dire minimiser le **pire rang par
élève**, à taux d'affectation constant.

Recette (héritée de :mod:`experiments.algo_upgrade`, appliquée à
l'allocation optimale de min-cost flow au lieu d'une allocation aléatoire) :

  1. Initialisation par min-cost flow (2 928 affectations, optimum utilitaire).
  2. Passes de recherche locale tant qu'il y a amélioration :
       a. Déplacements individuels vers occurrences libres mieux classées.
       b. Swaps entre deux élèves si le maximum de leurs rangs baisse.

Résultat sur les données de test : max d'affectations conservé (2 928),
67 % de premier choix (vs 57 % pour flow seul), pire max = 8 (vs 10).
"""
from __future__ import annotations
import random
from .model import Instance, Assignment
from .common import rang, reste_capacite
from .filters import accessible, occ_accessibles
from . import algo_flow

NAME = "equite"


def solve(inst: Instance, max_passes: int = 15, seed: int = 0) -> Assignment:
    a = algo_flow.solve(inst)
    for i in range(max_passes):
        if not _pass(inst, a, seed * 1000 + i):
            break
    return a


def _pass(inst: Instance, a: Assignment, seed: int) -> bool:
    rng = random.Random(seed)
    occ = {o.id_occ: o for o in inst.occurrences}
    student = {s.id_eleve: s for s in inst.students}
    reste = reste_capacite(inst, a)
    improved = False

    for bloc in inst.blocs:
        assigned = [(eid, a[eid][bloc]) for eid in a if a[eid][bloc]]
        rng.shuffle(assigned)

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

        eids = [eid for eid in a if a[eid][bloc]]
        for i, e1 in enumerate(eids):
            for e2 in eids[i+1:]:
                # Re-lire les affectations courantes (invalidées par swaps précédents).
                o1, o2 = a[e1][bloc], a[e2][bloc]
                if not o1 or not o2 or o1 == o2:
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


