"""Affectation bipartie (algorithme hongrois, §13.3).

L'algo hongrois est un-à-un. Pour gérer les capacités > 1, on **duplique**
chaque occurrence ``c`` fois (une copie par place). Traitement par bloc car
la matrice devient carrée par ajout de colonnes fictives à coût prohibitif
si le total des capacités ne couvre pas tous les élèves.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import linear_sum_assignment
from .model import Instance, Assignment
from .common import cout, empty_assignment
from .filters import accessible

from .constantes import BIG_M

NAME = "hungarian"


def solve(inst: Instance) -> Assignment:
    result = empty_assignment(inst)
    for bloc in inst.blocs:
        _solve_bloc(inst, bloc, result)
    return result


def _solve_bloc(inst: Instance, bloc: str, result: Assignment) -> None:
    students = inst.students
    occs = [o for o in inst.occ_by_bloc(bloc) if o.cap_dispo > 0]
    # Duplique chaque occurrence cap_dispo fois.
    slots: list[tuple[str, int]] = [(o.id_occ, k) for o in occs for k in range(o.cap_dispo)]
    n, m = len(students), len(slots)
    dim = max(n, m)
    C = np.full((dim, dim), BIG_M, dtype=int)
    occ_by_id = {o.id_occ: o for o in occs}

    for i, s in enumerate(students):
        for j, (oid, _) in enumerate(slots):
            o = occ_by_id[oid]
            if accessible(s, o):
                C[i, j] = cout(s, o)

    rows, cols = linear_sum_assignment(C)
    for i, j in zip(rows, cols):
        if i < n and j < m and C[i, j] < BIG_M:
            result[students[i].id_eleve][bloc] = slots[j][0]
