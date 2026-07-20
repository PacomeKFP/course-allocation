"""Rapport post-affectation : non-affectés + causes, remplissage, statistiques.

``Report`` est une façade qui retourne des ``pandas.DataFrame`` prêts à
sérialiser ou afficher. Chaque section vit dans sa propre méthode.
"""
from __future__ import annotations
from collections import Counter
import pandas as pd
from ..data.model import Campaign, Assignment
from ..rules import Feasibility
from ..solvers.base import rank


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
        rows = [{
            "id_occ": o.id_occ, "code_ue": o.code_ue, "label": o.label,
            "period": o.period, "slot": o.slot, "language": o.language,
            "fisea": o.fisea, "cap_min": o.cap_min, "cap_max": o.cap_max,
            "n_enrolled": used[o.id_occ] + o.already_enrolled,
            "under_min": (used[o.id_occ] + o.already_enrolled) < o.cap_min,
            "over_max": (used[o.id_occ] + o.already_enrolled) > o.cap_max,
        } for o in self.c.occurrences.values()]
        return pd.DataFrame(rows).sort_values(["period", "slot"])

    def stats_global(self) -> dict:
        """Distribution globale des rangs obtenus (1er choix, 2e, …)."""
        ranks = self._obtained_ranks()
        dist = Counter(ranks)
        n = len(ranks)
        return {"n_expected": len(self.c.voeux), "n_assigned": n,
                "assignment_rate": n / len(self.c.voeux) if self.c.voeux else 0,
                "rank_distribution": dict(sorted(dist.items())),
                "first_choice_share": dist.get(1, 0) / n if n else 0,
                "top3_share": sum(v for k, v in dist.items() if k <= 3) / n if n else 0}

    def stats_per_demande(self) -> pd.DataFrame:
        """Distribution des rangs par IDDemande."""
        rows = []
        for id_demande in self.c.demandes():
            ranks = [rank(v, self.a[(v.id_student, v.id_demande)])
                     for v in self.c.voeux
                     if v.id_demande == id_demande
                     and self.a.get((v.id_student, v.id_demande))]
            if ranks:
                d = Counter(ranks)
                rows.append({"id_demande": id_demande, "n": len(ranks),
                             "first_choice": d.get(1, 0), "avg_rank": sum(ranks) / len(ranks),
                             "worst_rank": max(ranks)})
        return pd.DataFrame(rows)

    def stats_compensation(self) -> pd.DataFrame:
        """Compensation inter-demandes : pire rang, somme des rangs par élève."""
        by_student: dict[str, list[int]] = {}
        for v in self.c.voeux:
            id_occ = self.a.get((v.id_student, v.id_demande))
            if id_occ:
                by_student.setdefault(v.id_student, []).append(rank(v, id_occ))
        return pd.DataFrame([{"id_student": sid, "n_assigned": len(rs),
                              "avg_rank": sum(rs) / len(rs), "worst_rank": max(rs),
                              "sum_ranks": sum(rs)} for sid, rs in by_student.items()])

    def _diagnose(self, s, v) -> str:
        """Reconstruit la raison de non-affectation avec ventilation détaillée.

        Décompte pour chaque vœu classé : occurrence inconnue / raison de
        rejet Feasibility / occurrence saturée. Retourne un résumé lisible.
        """
        if not v.ranked_occurrences:
            return "aucun vœu classé pour cette demande"
        n_total = len(v.ranked_occurrences)
        n_unknown = n_creneau = n_fisea = n_slot = n_jour = n_langue = n_pleine = 0
        for oid in v.ranked_occurrences:
            o = self.c.occurrences.get(oid)
            if o is None:
                n_unknown += 1; continue
            reasons = self.f.check(s, o)
            if not reasons:
                n_pleine += 1
                continue
            for msg in reasons:
                if "créneau non fixé" in msg: n_creneau += 1
                elif "FISEA" in msg: n_fisea += 1
                elif "occupé par filière" in msg: n_slot += 1
                elif "entreprise" in msg: n_jour += 1
                elif "français, élève anglophone" in msg: n_langue += 1
        parts = []
        if n_pleine: parts.append(f"{n_pleine} vœu(x) saturé(s)")
        if n_slot: parts.append(f"{n_slot} conflit(s) avec créneau de filière")
        if n_jour: parts.append(f"{n_jour} tombe(nt) sur jour d'entreprise")
        if n_langue: parts.append(f"{n_langue} en français (élève anglophone)")
        if n_fisea: parts.append(f"{n_fisea} réservé(s) apprentis")
        if n_creneau: parts.append(f"{n_creneau} sans créneau fixé")
        if n_unknown: parts.append(f"{n_unknown} occurrence(s) inconnue(s)")
        return f"sur {n_total} vœu(x) : " + " ; ".join(parts) if parts else "cause indéterminée"

    def _obtained_ranks(self) -> list[int]:
        return [rank(v, self.a[(v.id_student, v.id_demande)])
                for v in self.c.voeux if self.a.get((v.id_student, v.id_demande))]
