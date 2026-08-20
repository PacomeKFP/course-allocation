"""Solveur MIP (CP-SAT) — toutes les règles encodées comme contraintes.

Modèle : ``x[(id_student, id_demande, id_occ)] ∈ {0,1}`` pour les
occurrences classées ET accessibles ; chaque paire (élève, demande) obtient
1 occ ou un slack pénalisé ; capacité, exclusions inter-occ **par élève**
(même instant, même UE), unicité UE ; objectif = ``Σ rang^p × x + BIG_M × slacks``.
"""
from __future__ import annotations
from collections import Counter
from ortools.sat.python import cp_model
from ..data.model import Assignment
from ..data.constants import BIG_M, COST_POWER, ENGLISH_MATCH_BONUS
from ..rules import StudentConstraints
from ..utils import group_by
from .base import Solver, empty_assignment, rank


class MipSolver(Solver):
    NAME = "mip"

    def __init__(self, cost_power=COST_POWER, english_bonus=ENGLISH_MATCH_BONUS,
                 time_limit_s=60.0, workers=8):
        self.cost_power, self.english_bonus = cost_power, english_bonus
        self.time_limit_s, self.workers = time_limit_s, workers

    def solve(self, campaign, pre_assignment=None) -> Assignment:
        pre = pre_assignment or {}
        served = {k for k, v in pre.items() if v}
        m = cp_model.CpModel()
        forbidden = StudentConstraints().build(campaign)
        x, slacks, by_occ, by_student = self._variables(m, campaign, forbidden, served)
        self._one_per_demande(m, campaign, x, slacks, served)
        self._capacity(m, campaign, by_occ, pre)
        self._exclusions(m, campaign, by_student, pre)
        self._objective(m, campaign, x, slacks)
        return self._extract(m, campaign, x, pre)

    def _variables(self, m, campaign, forbidden, served):
        x, slacks, by_occ, by_student = {}, {}, {}, {}
        for v in campaign.voeux:
            if (v.id_student, v.id_demande) in served:
                continue
            for id_occ in v.ranked_occurrences:
                if (v.id_student, id_occ) in forbidden or id_occ not in campaign.occurrences:
                    continue
                var = m.NewBoolVar(f"x_{v.id_student}_{v.id_demande}_{id_occ}")
                x[(v.id_student, v.id_demande, id_occ)] = var
                by_occ.setdefault(id_occ, []).append(var)
                by_student.setdefault(v.id_student, []).append((id_occ, var))
            slacks[(v.id_student, v.id_demande)] = m.NewBoolVar(
                f"u_{v.id_student}_{v.id_demande}")
        return x, slacks, by_occ, by_student

    def _one_per_demande(self, m, campaign, x, slacks, served):
        for v in campaign.voeux:
            if (v.id_student, v.id_demande) in served:
                continue
            xs = [x[(v.id_student, v.id_demande, o)] for o in v.ranked_occurrences
                  if (v.id_student, v.id_demande, o) in x]
            m.Add(sum(xs) + slacks[(v.id_student, v.id_demande)] == 1)

    def _capacity(self, m, campaign, by_occ, pre):
        used = Counter(oid for oid in pre.values() if oid)
        for id_occ, o in campaign.occurrences.items():
            vs = by_occ.get(id_occ, [])
            if vs:
                m.Add(sum(vs) <= max(0, o.cap_available - used[id_occ]))

    def _exclusions(self, m, campaign, by_student, pre):
        """Par élève : au plus 1 occurrence par instant et par UE, toutes
        demandes confondues — pré-affectations comprises (constantes)."""
        occs = campaign.occurrences
        pre_by_student = group_by(((sid, oid) for (sid, _), oid in pre.items() if oid),
                                  key=lambda t: t[0])
        sids = set(by_student) | set(pre_by_student)
        for sid in sids:
            # (id_occ, variable | None) — None = pré-affectation déjà acquise
            entries = list(by_student.get(sid, []))
            entries += [(oid, None) for _, oid in pre_by_student.get(sid, [])]
            entries = [(oid, var) for oid, var in entries if oid in occs]
            for keyf in (lambda o: (o.period, o.slot), lambda o: o.id_ue):
                for bucket in group_by(entries, lambda e: keyf(occs[e[0]])).values():
                    vars_ = [var for _, var in bucket if var is not None]
                    n_fixed = len(bucket) - len(vars_)
                    if n_fixed and vars_:
                        m.Add(sum(vars_) == 0)  # créneau/UE déjà pris par une priorité
                    elif len(vars_) > 1:
                        m.Add(sum(vars_) <= 1)

    def _objective(self, m, campaign, x, slacks):
        terms = [BIG_M * sl for sl in slacks.values()]
        for v in campaign.voeux:
            for id_occ in v.ranked_occurrences:
                if (v.id_student, v.id_demande, id_occ) not in x:
                    continue
                r = rank(v, id_occ) ** self.cost_power
                o, s = campaign.occurrences[id_occ], campaign.students[v.id_student]
                if not s.francophone and o.language == "EN":
                    r = max(1, r - self.english_bonus)
                terms.append(r * x[(v.id_student, v.id_demande, id_occ)])
        m.Minimize(sum(terms))

    def _extract(self, m, campaign, x, pre):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_s
        solver.parameters.num_search_workers = self.workers
        status = solver.Solve(m)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError(f"CP-SAT: {solver.StatusName(status)}")
        result = empty_assignment(campaign) | {k: v for k, v in pre.items() if v}
        result.update({(sid, did): id_occ for (sid, did, id_occ), var in x.items()
                       if solver.Value(var) == 1})
        return result
