"""Solveur MIP (CP-SAT) — toutes les règles encodées comme contraintes.

Modèle : ``x[(id_student, id_demande, id_occ)] ∈ {0,1}`` pour les
occurrences classées ET accessibles ; chaque paire (élève, demande) obtient
1 occ ou un slack pénalisé ; capacité, exclusions inter-occ, unicité UE ;
objectif = ``Σ rang^p × x + BIG_M × slacks``.
"""
from __future__ import annotations
from collections import Counter
from ortools.sat.python import cp_model
from ..data.model import Assignment
from ..data.constants import BIG_M, COST_POWER, ENGLISH_MATCH_BONUS
from ..rules import OccurrenceConstraints, StudentConstraints
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
        x, slacks = self._variables(m, campaign, forbidden, served)
        self._one_per_demande(m, campaign, x, slacks, served)
        self._capacity(m, campaign, x, pre)
        self._exclusions(m, campaign, x)
        self._objective(m, campaign, x, slacks)
        return self._extract(m, campaign, x, pre)

    def _variables(self, m, campaign, forbidden, served):
        x, slacks = {}, {}
        for v in campaign.voeux:
            if (v.id_student, v.id_demande) in served:
                continue
            for id_occ in v.ranked_occurrences:
                if (v.id_student, id_occ) in forbidden or id_occ not in campaign.occurrences:
                    continue
                x[(v.id_student, v.id_demande, id_occ)] = m.NewBoolVar(
                    f"x_{v.id_student}_{v.id_demande}_{id_occ}")
            slacks[(v.id_student, v.id_demande)] = m.NewBoolVar(
                f"u_{v.id_student}_{v.id_demande}")
        return x, slacks

    def _one_per_demande(self, m, campaign, x, slacks, served):
        for v in campaign.voeux:
            if (v.id_student, v.id_demande) in served:
                continue
            xs = [x[(v.id_student, v.id_demande, o)] for o in v.ranked_occurrences
                  if (v.id_student, v.id_demande, o) in x]
            m.Add(sum(xs) + slacks[(v.id_student, v.id_demande)] == 1)

    def _capacity(self, m, campaign, x, pre):
        used = Counter(oid for oid in pre.values() if oid)
        for id_occ, o in campaign.occurrences.items():
            vs = [x[k] for k in x if k[2] == id_occ]
            if vs:
                m.Add(sum(vs) <= max(0, o.cap_available - used[id_occ]))

    def _exclusions(self, m, campaign, x):
        for group in OccurrenceConstraints().build(campaign.occurrences):
            for v in campaign.voeux:
                vs = [x[(v.id_student, v.id_demande, o)] for o in group
                      if (v.id_student, v.id_demande, o) in x]
                if len(vs) > 1:
                    m.Add(sum(vs) <= 1)

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
