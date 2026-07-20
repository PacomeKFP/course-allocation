"""Rapport post-affectation — DataFrames prêts à sérialiser ou afficher."""
from __future__ import annotations
from collections import Counter
import pandas as pd
from ..data.model import Campaign, Assignment
from ..rules import Feasibility
from ..solvers.base import rank

_LABELS = [("créneau non fixé", "sans créneau fixé"),
           ("FISEA", "réservé(s) apprentis"),
           ("occupé par filière", "conflit(s) avec créneau de filière"),
           ("entreprise", "tombe(nt) sur jour d'entreprise"),
           ("français, élève anglophone", "en français (élève anglophone)")]

def _CAUSE_LABEL(msg: str) -> str:
    return next((lbl for key, lbl in _LABELS if key in msg), "autre raison")


class Report:
    def __init__(self, campaign: Campaign, assignment: Assignment,
                 feasibility: Feasibility | None = None):
        self.c = campaign
        self.a = assignment
        self.f = feasibility or Feasibility()

    def not_assigned(self) -> pd.DataFrame:
        """Liste des paires (élève, demande) non affectées, avec cause."""
        rows = []
        for v in self.c.voeux:
            if self.a.get((v.id_student, v.id_demande)):
                continue
            s = self.c.students[v.id_student]
            reasons = self._diagnose(s, v)
            rows.append({"id_student": s.id_student, "id_demande": v.id_demande,
                         "regime": s.regime, "filieres": "+".join(s.filieres),
                         "n_voeux": len(v.ranked_occurrences), "cause": reasons})
        return pd.DataFrame(rows)

    def filling(self) -> pd.DataFrame:
        """Occurrences avec effectif final vs min/max — style ECUE enrichi."""
        used = Counter(oid for oid in self.a.values() if oid)
        def row(o):
            n = used[o.id_occ] + o.already_enrolled
            return {"id_occ": o.id_occ, "code_ue": o.code_ue, "label": o.label,
                    "period": o.period, "slot": o.slot, "language": o.language,
                    "fisea": o.fisea, "cap_min": o.cap_min, "cap_max": o.cap_max,
                    "n_enrolled": n, "under_min": n < o.cap_min, "over_max": n > o.cap_max}
        return pd.DataFrame([row(o) for o in self.c.occurrences.values()]
                            ).sort_values(["period", "slot"])

    def stats_global(self) -> dict:
        """Distribution globale des rangs obtenus (1er choix, 2e, …)."""
        rs = self._obtained_ranks(); d = Counter(rs); n = len(rs)
        return {"n_expected": len(self.c.voeux), "n_assigned": n,
                "assignment_rate": n / len(self.c.voeux) if self.c.voeux else 0,
                "rank_distribution": dict(sorted(d.items())),
                "first_choice_share": d.get(1, 0) / n if n else 0,
                "top3_share": sum(v for k, v in d.items() if k <= 3) / n if n else 0}

    def stats_per_demande(self) -> pd.DataFrame:
        """Distribution des rangs par IDDemande."""
        rows = []
        for d in self.c.demandes():
            rs = [rank(v, self.a[(v.id_student, v.id_demande)]) for v in self.c.voeux
                  if v.id_demande == d and self.a.get((v.id_student, v.id_demande))]
            if rs:
                rows.append({"id_demande": d, "n": len(rs),
                             "first_choice": Counter(rs).get(1, 0),
                             "avg_rank": sum(rs) / len(rs), "worst_rank": max(rs)})
        return pd.DataFrame(rows)

    def stats_compensation(self) -> pd.DataFrame:
        """Compensation inter-demandes : pire rang, somme des rangs par élève."""
        by_s: dict[str, list[int]] = {}
        for v in self.c.voeux:
            oid = self.a.get((v.id_student, v.id_demande))
            if oid: by_s.setdefault(v.id_student, []).append(rank(v, oid))
        return pd.DataFrame([{"id_student": sid, "n_assigned": len(rs),
                              "avg_rank": sum(rs)/len(rs), "worst_rank": max(rs),
                              "sum_ranks": sum(rs)} for sid, rs in by_s.items()])

    def _diagnose(self, s, v) -> str:
        """Ventile les vœux par cause : saturé / filière / entreprise / langue…"""
        if not v.ranked_occurrences:
            return "aucun vœu classé pour cette demande"
        buckets = Counter()
        for oid in v.ranked_occurrences:
            o = self.c.occurrences.get(oid)
            if o is None:
                buckets["occurrence(s) inconnue(s)"] += 1; continue
            reasons = self.f.check(s, o)
            if not reasons:
                buckets["vœu(x) saturé(s)"] += 1; continue
            for msg in reasons:
                buckets[_CAUSE_LABEL(msg)] += 1
        parts = [f"{n} {lbl}" for lbl, n in buckets.most_common()]
        return f"sur {len(v.ranked_occurrences)} vœu(x) : " + " ; ".join(parts)

    def _obtained_ranks(self):
        return [rank(v, self.a[(v.id_student, v.id_demande)]) for v in self.c.voeux
                if self.a.get((v.id_student, v.id_demande))]
