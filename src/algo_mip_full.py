"""MIP intégral (CP-SAT) — toutes les règles métier encodées comme contraintes.

Motivation : les algos courants (flow, hungarian, equite) résolvent bloc
par bloc. Rien n'empêche mathématiquement qu'un élève reçoive deux cours
de blocs différents au même moment. Ce solveur adresse ce trou en
encodant toutes les règles simultanément.

Règles encodées :

  1. **Accessibilité** — filière, langue, FISEA, jours d'entreprise.
     Pré-filtrage : seules les paires (élève, occ) accessibles deviennent
     des variables.
  2. **Exclusion inter-occurrences par instant** — deux occurrences au
     même (période, créneau) sont mutuellement exclusives pour un élève.
  3. **Unicité ECUE dans l'année** — un ECUE ne peut être suivi qu'une
     seule fois, même s'il apparaît dans plusieurs occurrences.
  4. **Complétude par régime** :
     - FISE : exactement 1 occurrence par bloc — pénalité BIG_M par
       bloc non affecté.
     - FISEA : au plus 3 ECUE par semestre + bonus qui encourage
       l'atteinte de la cible.
  5. **Capacité** — nombre d'affectations ≤ capacité disponible.

Objectif : minimiser ``sum(coût × x) + BIG_M × slacks + λ × tau_max`` où
``tau_max`` borne le taux de remplissage maximum sur toutes les occurrences.
"""
from __future__ import annotations
from copy import deepcopy
from ortools.sat.python import cp_model
from .model import Instance, Assignment
from .common import cout, empty_assignment
from .filters import accessible
from .constantes import semestre_de_periode
from .algo_mip import BIG_M

NAME = "mip_full"
LAMBDA_EQUILIBRE = 50


def _group_by(items, key_fn):
    groups: dict = {}
    for it in items:
        groups.setdefault(key_fn(it), []).append(it)
    return groups


def _split_modules(inst: Instance) -> Instance:
    """Scinde tout bloc « Module d'ouverture » en (S1) et (S2)."""
    inst = deepcopy(inst)
    for o in inst.occurrences:
        if "Module d'ouverture" in o.bloc:
            o.bloc = f"{o.bloc.rstrip()} (S{semestre_de_periode(o.periode)})"
    inst.blocs = sorted({o.bloc for o in inst.occurrences})
    base = lambda b: b.split(" (S")[0].strip() if "Module d'ouverture" in b else b
    for s in inst.students:
        s.voeux_par_bloc = {b: s.voeux_par_bloc.get(base(b), []) for b in inst.blocs}
    return inst


def solve(inst: Instance, time_limit_s: float = 60.0, workers: int = 8) -> Assignment:
    inst = _split_modules(inst)
    m = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    par_occ: dict[str, list] = {o.id_occ: [] for o in inst.occurrences}
    cost_terms = []

    # Variables + coûts + indexation par occurrence en une seule passe.
    for s in inst.students:
        for o in inst.occurrences:
            if not accessible(s, o):
                continue
            v = m.NewBoolVar(f"x_{s.id_eleve}_{o.id_occ}")
            x[(s.id_eleve, o.id_occ)] = v
            par_occ[o.id_occ].append(v)
            cost_terms.append(cout(s, o) * v)

    par_instant = _group_by(inst.occurrences, lambda o: (o.periode, o.creneau))
    par_ue = _group_by(inst.occurrences, lambda o: o.id_ue)
    par_bloc = _group_by(inst.occurrences, lambda o: o.bloc)
    par_sem = _group_by(inst.occurrences, lambda o: semestre_de_periode(o.periode))

    # (2) + (3) exclusions mutuelles : au plus 1 occ par instant ET par ECUE.
    for s in inst.students:
        for buckets in (par_instant.values(), par_ue.values()):
            for occs in buckets:
                vs = [v for o in occs
                      if (v := x.get((s.id_eleve, o.id_occ))) is not None]
                if len(vs) > 1:
                    m.Add(sum(vs) <= 1)

    # (4) Complétude selon régime.
    for s in inst.students:
        if s.regime == "apprenti":
            for sem in (1, 2):
                v_sem = [v for o in par_sem.get(sem, [])
                         if (v := x.get((s.id_eleve, o.id_occ))) is not None]
                if v_sem:
                    m.Add(sum(v_sem) <= 3)
                    # -BIG_M · v_sem = -BIG_M · sum(v_sem) + constante ignorée.
                    cost_terms.extend(-BIG_M * v for v in v_sem)
        else:
            for bloc, occs in par_bloc.items():
                v_bloc = [v for o in occs
                          if (v := x.get((s.id_eleve, o.id_occ))) is not None]
                sl = m.NewBoolVar(f"u_{s.id_eleve}_{bloc}")
                m.Add(sum(v_bloc) + sl == 1)
                cost_terms.append(BIG_M * sl)

    # (5) Capacité + équilibrage : mêmes vs = par_occ[oid], une seule boucle.
    tau_max = m.NewIntVar(0, 100, "tau_max")
    for o in inst.occurrences:
        vs = par_occ[o.id_occ]
        if not vs:
            continue
        m.Add(sum(vs) <= o.cap_dispo)
        if o.cap_dispo > 0:
            m.Add(100 * sum(vs) <= tau_max * o.cap_dispo)

    m.Minimize(sum(cost_terms) + LAMBDA_EQUILIBRE * tau_max)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = workers
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"CP-SAT: {solver.StatusName(status)}")
    print(f"  [mip_full] {solver.StatusName(status)} "
          f"obj={solver.ObjectiveValue():.0f} tau_max={solver.Value(tau_max)}%")

    bloc_of = {o.id_occ: o.bloc for o in inst.occurrences}
    result = empty_assignment(inst)
    for (eid, oid), v in x.items():
        if solver.Value(v) == 1:
            result[eid][bloc_of[oid]] = oid
    return result
