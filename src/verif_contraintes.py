"""Vérification exhaustive des contraintes sur une affectation.

Un algo peut violer silencieusement certaines contraintes (ex : flow et
equite ignorent les collisions inter-blocs). Ce module recontrôle *tout*
sur la sortie et signale chaque violation.

Contraintes vérifiées :
  1. **Accessibilité** — chaque affectation respecte créneau/langue/FISEA/
     jours d'entreprise (via ``filters.raison_rejet``).
  2. **Exclusion instant** — aucun élève n'a deux cours au même
     ``(période, créneau)``.
  3. **Unicité ECUE** — aucun élève ne suit deux fois le même code UE.
  4. **Capacité** — aucune occurrence ne dépasse ``cap_dispo``.
  5. **Complétude** — FISE : ≤ 1 occurrence par bloc de vœux ;
     FISEA : ≤ 3 ECUE par semestre.
  6. **Charge** — chaque élève atteint la cible de crédits (2,5 × bloc).

Toutes les fonctions renvoient ``(n_violations, DataFrame)``.
"""
from __future__ import annotations
from collections import Counter
import pandas as pd
from .model import Instance, Assignment
from .filters import raison_rejet
from .constantes import semestre_de_periode

CREDITS_PAR_BLOC = 2.5
CIBLE_FISE = 15.0
CIBLE_FISEA = 7.5   # 3 ECUE × 2.5 crédits par semestre × 2 semestres / 2 = 7.5


def _assigns(inst: Instance, a: Assignment):
    """Génère les tuples (student, occ) affectés."""
    for s in inst.students:
        for oid in a[s.id_eleve].values():
            if oid:
                yield s, inst.occ_by_id(oid)


def accessibilite(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Affectations où la paire (élève, occ) n'est pas accessible."""
    return pd.DataFrame([
        {"eleve": s.id_eleve, "id_occ": o.id_occ, "raison": raison_rejet(s, o)}
        for s, o in _assigns(inst, a) if raison_rejet(s, o)
    ])


def exclusion_instant(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Élèves ayant plusieurs cours au même ``(période, créneau)``."""
    rows = []
    for s in inst.students:
        instants = [(inst.occ_by_id(oid).periode, inst.occ_by_id(oid).creneau)
                    for oid in a[s.id_eleve].values() if oid]
        for inst_key, n in Counter(instants).items():
            if n > 1:
                rows.append({"eleve": s.id_eleve, "periode": inst_key[0],
                             "creneau": inst_key[1], "n_cours": n})
    return pd.DataFrame(rows)


def unicite_ecue(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Élèves ayant deux occurrences du même ECUE."""
    rows = []
    for s in inst.students:
        ues = [inst.occ_by_id(oid).id_ue for oid in a[s.id_eleve].values() if oid]
        for ue, n in Counter(ues).items():
            if n > 1:
                rows.append({"eleve": s.id_eleve, "id_ue": ue, "n_fois": n})
    return pd.DataFrame(rows)


def capacite(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Occurrences en dépassement de capacité."""
    used = Counter(oid for eid in a for oid in a[eid].values() if oid)
    rows = []
    for o in inst.occurrences:
        n = used[o.id_occ] + o.nb_deja_inscrits
        if n > o.cap_max:
            rows.append({"id_occ": o.id_occ, "id_display": o.id_display,
                         "n_effectif": n, "cap_max": o.cap_max,
                         "depassement": n - o.cap_max})
    return pd.DataFrame(rows)


def completude(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Violations : FISE avec > 1 par bloc, FISEA avec > 3 ECUE par semestre."""
    rows = []
    for s in inst.students:
        per_bloc = Counter(inst.occ_by_id(oid).bloc
                           for oid in a[s.id_eleve].values() if oid)
        per_sem = Counter(semestre_de_periode(inst.occ_by_id(oid).periode)
                          for oid in a[s.id_eleve].values() if oid)
        for bloc, n in per_bloc.items():
            if n > 1:
                rows.append({"eleve": s.id_eleve, "type": "bloc>1",
                             "detail": bloc, "n": n})
        if s.regime == "apprenti":
            for sem, n in per_sem.items():
                if n > 3:
                    rows.append({"eleve": s.id_eleve, "type": "fisea_sem>3",
                                 "detail": f"S{sem}", "n": n})
    return pd.DataFrame(rows)


def charge(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Élèves sous la cible de crédits attendue par leur régime."""
    rows = []
    for s in inst.students:
        n = sum(1 for oid in a[s.id_eleve].values() if oid)
        credits = n * CREDITS_PAR_BLOC
        cible = CIBLE_FISEA if s.regime == "apprenti" else CIBLE_FISE
        if credits < cible:
            rows.append({"eleve": s.id_eleve, "regime": s.regime,
                         "n_blocs": n, "credits": credits, "cible": cible})
    return pd.DataFrame(rows)


CHECKS = {
    "accessibilite": accessibilite,
    "exclusion_instant": exclusion_instant,
    "unicite_ecue": unicite_ecue,
    "capacite": capacite,
    "completude": completude,
    "charge": charge,
}


def verifier(inst: Instance, a: Assignment) -> dict:
    """Applique toutes les vérifications, renvoie un résumé + DataFrames détaillés."""
    details = {name: fn(inst, a) for name, fn in CHECKS.items()}
    resume = {name: len(df) for name, df in details.items()}
    resume["total_violations"] = sum(resume.values())
    return {"resume": resume, "details": details}


def print_rapport(inst: Instance, a: Assignment) -> None:
    r = verifier(inst, a)
    print("Vérification des contraintes :")
    for k, v in r["resume"].items():
        marque = "OK" if v == 0 else f"VIOLATIONS ({v})"
        print(f"  {k:<25} {marque}")
    for name, df in r["details"].items():
        if len(df):
            print(f"\n  Détails {name} (5 premiers) :")
            print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    import sys
    from .preprocess import load
    from .algo_equite import solve
    inst = load(sys.argv[1] if len(sys.argv) > 1 else "data")
    print_rapport(inst, solve(inst))
