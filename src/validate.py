"""Validation d'une affectation — savoir si un résultat est correct, et pourquoi
une demande est (ou n'est pas) satisfiable.

Deux entrées publiques :

* ``validate_assignment(campaign, assignment)`` : vérifie **toutes** les règles
  dures sur le résultat (faisabilité, capacité, unicité UE, exclusion horaire,
  un vœu au plus par demande). Renvoie la liste des violations — vide = correct.
* ``analyze_demande(campaign, id_student, id_demande)`` : ventile les vœux
  d'une paire (élève, demande) entre *impossibles* (règle dure) et *possibles*
  (seule la capacité peut bloquer) — explicabilité avant/après résolution.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field

from .data.model import Campaign, Assignment
from .rules import Feasibility


@dataclass
class Violation:
    kind: str            # "infaisable" | "capacité" | "conflit_horaire" | "ue_en_double" | "hors_voeux"
    detail: str


def validate_assignment(campaign: Campaign, assignment: Assignment,
                        feasibility: Feasibility | None = None) -> list[Violation]:
    """Liste des violations de règles dures ; vide ⟺ affectation correcte."""
    f = feasibility or Feasibility()
    violations: list[Violation] = []
    given = {k: oid for k, oid in assignment.items() if oid}

    # 1. Chaque affectation est un vœu classé, faisable, et l'occurrence existe.
    for (sid, did), oid in given.items():
        o = campaign.occurrences.get(oid)
        s = campaign.students.get(sid)
        v = campaign.voeu_of(sid, did)
        if o is None or s is None:
            violations.append(Violation("hors_voeux", f"{sid}/{did} → occurrence ou élève inconnu"))
            continue
        if v is None or oid not in v.ranked_occurrences:
            violations.append(Violation("hors_voeux", f"{sid}/{did} → {oid} non classé par l'élève"))
        reasons = f.check(s, o)
        if reasons:
            violations.append(Violation("infaisable", f"{sid}/{did} → {oid} : {'; '.join(reasons)}"))

    # 2. Capacité disponible respectée (inscrits préexistants compris).
    used = Counter(given.values())
    for oid, n in used.items():
        o = campaign.occurrences.get(oid)
        if o and n > o.cap_available:
            violations.append(Violation("capacité", f"{oid} : {n} affectés > {o.cap_available} places"))

    # 3. Par élève : jamais deux occurrences au même instant, jamais deux fois la même UE.
    by_student: dict[str, list[str]] = {}
    for (sid, _), oid in given.items():
        by_student.setdefault(sid, []).append(oid)
    for sid, oids in by_student.items():
        instants = [(o.period, o.slot) for oid in oids if (o := campaign.occurrences.get(oid))]
        ues = [o.id_ue for oid in oids if (o := campaign.occurrences.get(oid))]
        for instant, n in Counter(instants).items():
            if n > 1:
                violations.append(Violation("conflit_horaire", f"{sid} : {n} cours en {instant}"))
        for ue, n in Counter(ues).items():
            if n > 1:
                violations.append(Violation("ue_en_double", f"{sid} : UE {ue} affectée {n} fois"))
    return violations


@dataclass
class DemandeAnalysis:
    n_voeux: int
    impossibles: dict[str, list[str]] = field(default_factory=dict)  # oid → raisons
    possibles: list[str] = field(default_factory=list)               # faisables, capacité mise à part

    @property
    def satisfiable(self) -> bool:
        """True ⟺ au moins un vœu n'est bloqué par aucune règle dure."""
        return bool(self.possibles)


def analyze_demande(campaign: Campaign, id_student: str, id_demande: str,
                    feasibility: Feasibility | None = None) -> DemandeAnalysis:
    """Ce qui est possible / impossible pour une paire (élève, demande)."""
    f = feasibility or Feasibility()
    s = campaign.students[id_student]
    v = campaign.voeu_of(id_student, id_demande)
    ranked = v.ranked_occurrences if v else []
    out = DemandeAnalysis(n_voeux=len(ranked))
    for oid in ranked:
        o = campaign.occurrences.get(oid)
        reasons = ["occurrence inconnue"] if o is None else f.check(s, o)
        (out.impossibles.__setitem__(oid, reasons) if reasons
         else out.possibles.append(oid))
    return out
