"""Métriques et rapport (§10-§11 du cahier).

Fonctions pures : elles reçoivent (instance, assignment) et retournent des
structures dict/DataFrame. Aucun côté effet.

Convention de rang : **1-indexé** (1 = premier choix). Un rang de 0 n'a
plus de sens ici.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import statistics
import pandas as pd
from .model import Instance, Assignment
from .common import rang
from .filters import occ_accessibles


def rangs_obtenus(inst: Instance, a: Assignment) -> list[int]:
    """Rang 1-indexé obtenu par chaque paire (élève, bloc) affectée."""
    return [rang(s, inst.occ_by_id(oid)) + 1
            for s in inst.students
            for oid in a[s.id_eleve].values() if oid]


def distribution_rangs(inst: Instance, a: Assignment) -> pd.Series:
    rs = rangs_obtenus(inst, a)
    if not rs:
        return pd.Series(dtype=int)
    return pd.Series(Counter(rs)).sort_index()


def _paires_attendues(inst: Instance) -> int:
    """Paires (élève, bloc) où l'élève a exprimé au moins un vœu (§note 10)."""
    return sum(1 for s in inst.students for b in inst.blocs if s.voeux_par_bloc.get(b))


def non_affectes(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Une ligne par (élève, bloc) non affecté avec la cause probable et l'identité de l'élève."""
    rows = []
    for s in inst.students:
        for b in inst.blocs:
            if a[s.id_eleve][b] is None and s.voeux_par_bloc.get(b):
                accs = occ_accessibles(inst, s, b)
                if not accs:
                    cause = "aucune occurrence accessible (créneau/langue/FISEA)"
                elif not any(o.id_ue in s.voeux_par_bloc[b] for o in accs):
                    cause = "vœux classés hors des occurrences accessibles"
                else:
                    cause = "toutes les occurrences accessibles étaient pleines"
                rows.append({
                    "eleve": s.id_eleve, "regime": s.regime, "langue": s.langue,
                    "groupes": "+".join(s.groupes_filiere) or "-",
                    "bloc": b, "cause": cause,
                    "n_voeux": len(s.voeux_par_bloc.get(b, [])),
                })
    return pd.DataFrame(rows)


def remplissage(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Places occupées par occurrence + alerte sous l'effectif min."""
    used = Counter()
    for s in inst.students:
        for oid in a[s.id_eleve].values():
            if oid:
                used[oid] += 1
    rows = []
    for o in inst.occurrences:
        total = used[o.id_occ] + o.nb_deja_inscrits
        rows.append({
            "id_occ": o.id_occ, "id_display": o.id_display,
            "bloc": o.bloc, "id_ue": o.id_ue,
            "intitule": o.intitule,
            "creneau": o.creneau, "periode": o.periode, "langue": o.langue,
            "fisea": o.fisea,
            "n_affectes_algo": used[o.id_occ],
            "n_deja_inscrits": o.nb_deja_inscrits,
            "n_total": total,
            "cap_min": o.cap_min, "cap_max": o.cap_max,
            "sous_min": total < o.cap_min and total > 0,
            "depasse_max": total > o.cap_max,
            "taux_remplissage": total / o.cap_max if o.cap_max else 0,
        })
    return pd.DataFrame(rows).sort_values(["bloc", "creneau"])


def equite_par_groupe(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Rang moyen et taux d'affectation par (régime, langue)."""
    by = defaultdict(list)
    aff = defaultdict(int)
    tot = defaultdict(int)
    for s in inst.students:
        key = (s.regime, s.langue)
        for b in inst.blocs:
            if not s.voeux_par_bloc.get(b):
                continue
            tot[key] += 1
            oid = a[s.id_eleve][b]
            if oid:
                aff[key] += 1
                by[key].append(rang(s, inst.occ_by_id(oid)) + 1)
    rows = []
    for key in tot:
        rs = by[key]
        rows.append({
            "regime": key[0], "langue": key[1],
            "n_paires": tot[key], "n_affectes": aff[key],
            "taux_aff": aff[key] / tot[key] if tot[key] else 0,
            "rang_moyen": sum(rs) / len(rs) if rs else float("nan"),
            "rang_median": statistics.median(rs) if rs else float("nan"),
            "rang_max": max(rs) if rs else 0,
        })
    return pd.DataFrame(rows)


def satisfaction_par_eleve(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Pour chaque élève : ses rangs par bloc + somme + max (= pire bloc)."""
    rows = []
    for s in inst.students:
        r_par_bloc = {}
        for b in inst.blocs:
            if not s.voeux_par_bloc.get(b):
                r_par_bloc[b] = None
                continue
            oid = a[s.id_eleve][b]
            r_par_bloc[b] = (rang(s, inst.occ_by_id(oid)) + 1) if oid else None
        obtenus = [r for r in r_par_bloc.values() if r is not None]
        rows.append({
            "eleve": s.id_eleve, "regime": s.regime, "langue": s.langue,
            "groupes": "+".join(s.groupes_filiere) or "-",
            **r_par_bloc,
            "somme_rangs": sum(obtenus) if obtenus else None,
            "pire_rang": max(obtenus) if obtenus else None,
            "meilleur_rang": min(obtenus) if obtenus else None,
            "n_affectes": sum(1 for x in r_par_bloc.values() if x is not None),
        })
    return pd.DataFrame(rows)


def resume(inst: Instance, a: Assignment) -> dict:
    rs = rangs_obtenus(inst, a)
    n_paires_attendues = _paires_attendues(inst)
    if not rs:
        return {"n_paires_attendues": n_paires_attendues, "n_affectations": 0}
    q = statistics.quantiles(rs, n=10) if len(rs) >= 10 else rs
    return {
        "n_paires_attendues": n_paires_attendues,
        "n_affectations": len(rs),
        "taux_affectation": len(rs) / n_paires_attendues if n_paires_attendues else 0,
        "rang_moyen": sum(rs) / len(rs),
        "rang_median": statistics.median(rs),
        "rang_min": min(rs),
        "rang_max": max(rs),
        "rang_q25": statistics.quantiles(rs, n=4)[0] if len(rs) >= 4 else float("nan"),
        "rang_q75": statistics.quantiles(rs, n=4)[2] if len(rs) >= 4 else float("nan"),
        "rang_d1": q[0] if len(rs) >= 10 else float("nan"),
        "rang_d9": q[-1] if len(rs) >= 10 else float("nan"),
        "part_1er_choix": sum(1 for r in rs if r == 1) / len(rs),
        "part_top3": sum(1 for r in rs if r <= 3) / len(rs),
        "part_rang_gte_5": sum(1 for r in rs if r >= 5) / len(rs),
    }


def export_assignment(inst: Instance, a: Assignment, path: str) -> None:
    """CSV lisible : une ligne par affectation (§11.1)."""
    rows = []
    for s in inst.students:
        for b, oid in a[s.id_eleve].items():
            rows.append({"eleveID": s.id_eleve, "bloc": b, "id_occ": oid or ""})
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)
