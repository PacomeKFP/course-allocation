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
     - FISE : exactement 1 occurrence par bloc de l'instance (avec
       Module d'ouverture scindé S1/S2 si présent) — pénalité BIG_M par
       bloc non affecté.
     - FISEA : au maximum 3 ECUE par semestre.
  5. **Capacité** — nombre d'affectations ≤ capacité disponible.

Objectif :
    sum(rang × x)             [utilitaire, 1er choix maximisé]
  + BIG_M × slack_non_affect  [complétude par bloc]
  + λ × tau_remplissage_max   [équilibrage entre occurrences]
"""
from __future__ import annotations
import sys
from copy import deepcopy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ortools.sat.python import cp_model
from src.model import Instance, Assignment
from src.common import rang, empty_assignment
from src.filters import accessible
from src.constantes import BONUS_ANGLOPHONE

NAME = "mip_full"
BIG_M = 10_000
LAMBDA_EQUILIBRE = 50


def _semestre(periode: int) -> int:
    return 1 if periode in (1, 2) else 2


def _split_modules(inst: Instance) -> Instance:
    """Scinde tout bloc « Module d'ouverture » en (S1) et (S2)."""
    inst = deepcopy(inst)
    for o in inst.occurrences:
        if "Module d'ouverture" in o.bloc:
            o.bloc = f"{o.bloc.rstrip()} (S{_semestre(o.periode)})"
    inst.blocs = sorted({o.bloc for o in inst.occurrences})
    for s in inst.students:
        new_vpb: dict[str, list[str]] = {}
        for b in inst.blocs:
            key = b.split(" (S")[0].strip() if "Module d'ouverture" in b else b
            new_vpb[b] = s.voeux_par_bloc.get(key, s.voeux_par_bloc.get(b, []))
        s.voeux_par_bloc = new_vpb
    return inst


def solve(inst: Instance, time_limit_s: float = 60.0, workers: int = 8) -> Assignment:
    inst = _split_modules(inst)
    m = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    slack: dict[tuple[str, str], cp_model.IntVar] = {}
    cost_terms = []

    for s in inst.students:
        for o in inst.occurrences:
            if not accessible(s, o):
                continue
            v = m.NewBoolVar(f"x_{s.id_eleve}_{o.id_occ}")
            x[(s.id_eleve, o.id_occ)] = v
            c = rang(s, o) + 1
            if s.langue == "EN" and o.langue == "EN":
                c -= BONUS_ANGLOPHONE
            cost_terms.append(c * v)

    # (2) Exclusion inter-occurrences au même instant.
    par_instant: dict[tuple[int, str], list] = {}
    for o in inst.occurrences:
        par_instant.setdefault((o.periode, o.creneau), []).append(o)
    for s in inst.students:
        for occs in par_instant.values():
            vs = [x[(s.id_eleve, o.id_occ)] for o in occs if (s.id_eleve, o.id_occ) in x]
            if len(vs) > 1:
                m.Add(sum(vs) <= 1)

    # (3) Unicité ECUE dans l'année.
    par_ue: dict[str, list] = {}
    for o in inst.occurrences:
        par_ue.setdefault(o.id_ue, []).append(o)
    for s in inst.students:
        for occs in par_ue.values():
            vs = [x[(s.id_eleve, o.id_occ)] for o in occs if (s.id_eleve, o.id_occ) in x]
            if len(vs) > 1:
                m.Add(sum(vs) <= 1)

    # (4) Complétude selon régime.
    for s in inst.students:
        if s.regime == "apprenti":
            for sem in (1, 2):
                v_sem = [x[(s.id_eleve, o.id_occ)] for o in inst.occurrences
                         if _semestre(o.periode) == sem and (s.id_eleve, o.id_occ) in x]
                if v_sem:
                    m.Add(sum(v_sem) <= 3)   # plafond dur : 3 ECUE / semestre
                    # Bonus (soft) sur ≥ 3 : on encourage 3 en pénalisant le manquant.
                    manque = m.NewIntVar(0, 3, f"manque_{s.id_eleve}_S{sem}")
                    m.Add(manque == 3 - sum(v_sem))
                    cost_terms.append(BIG_M * manque)
        else:
            # FISE : 1 occurrence par bloc, slack pénalisée.
            for bloc in inst.blocs:
                v_bloc = [x[(s.id_eleve, o.id_occ)] for o in inst.occ_by_bloc(bloc)
                          if (s.id_eleve, o.id_occ) in x]
                sl = m.NewBoolVar(f"u_{s.id_eleve}_{bloc}")
                slack[(s.id_eleve, bloc)] = sl
                m.Add(sum(v_bloc) + sl == 1) if v_bloc else m.Add(sl == 1)
                cost_terms.append(BIG_M * sl)

    # (5) Capacité par occurrence.
    for o in inst.occurrences:
        vs = [x[(s.id_eleve, o.id_occ)] for s in inst.students
              if (s.id_eleve, o.id_occ) in x]
        if vs:
            m.Add(sum(vs) <= o.cap_dispo)

    # Équilibrage : minimiser le taux de remplissage max (en pourcentage).
    tau_max = m.NewIntVar(0, 100, "tau_max")
    for o in inst.occurrences:
        vs = [x[(s.id_eleve, o.id_occ)] for s in inst.students
              if (s.id_eleve, o.id_occ) in x]
        if vs and o.cap_dispo > 0:
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

    result = empty_assignment(inst)
    for (eid, oid), v in x.items():
        if solver.Value(v) == 1:
            result[eid][inst.occ_by_id(oid).bloc] = oid
    return result
