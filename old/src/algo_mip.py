"""MIP global via OR-Tools CP-SAT (§13.1).

Modèle unique pour tous les blocs, exact. On expose le "non-affecté" comme
variable de slack pénalisée à BIG_M — équivalent à l'arc fallback du flot.
"""
from __future__ import annotations
from ortools.sat.python import cp_model
from .model import Instance, Assignment
from .common import couts_accessibles, empty_assignment
from .constantes import BIG_M

NAME = "mip"


def solve(inst: Instance, time_limit_s: float = 30.0) -> Assignment:
    m = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    u: dict[tuple[str, str], cp_model.IntVar] = {}  # slack "non-affecté"
    cout_terms = []

    for s in inst.students:
        for bloc in inst.blocs:
            slack = m.NewBoolVar(f"u_{s.id_eleve}_{bloc}")
            u[(s.id_eleve, bloc)] = slack
            xs = []
            for o, c in couts_accessibles(inst, s, bloc):
                v = m.NewBoolVar(f"x_{s.id_eleve}_{o.id_occ}")
                x[(s.id_eleve, o.id_occ)] = v
                xs.append(v)
                cout_terms.append(int(c) * v)
            m.Add(sum(xs) + slack == 1)
            cout_terms.append(BIG_M * slack)

    for o in inst.occurrences:
        vs = [x[(s.id_eleve, o.id_occ)] for s in inst.students
              if (s.id_eleve, o.id_occ) in x]
        if vs:
            m.Add(sum(vs) <= o.cap_dispo)

    m.Minimize(sum(cout_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT: pas de solution ({solver.StatusName(status)})")

    result = empty_assignment(inst)
    for (eid, oid), v in x.items():
        if solver.Value(v) == 1:
            bloc = inst.occ_by_id(oid).bloc
            result[eid][bloc] = oid
    return result
