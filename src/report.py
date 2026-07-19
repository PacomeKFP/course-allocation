"""Métriques et rapport (§10-§11 du cahier).

Fonctions pures : elles reçoivent (instance, assignment) et retournent des
structures dict/DataFrame. Aucun côté effet ; utilisées par le bench et l'app.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import pandas as pd
from .model import Instance, Assignment
from .common import rang
from .filters import occ_accessibles


def rangs(inst: Instance, a: Assignment) -> list[int]:
    """Rang (0-based) obtenu par chaque paire (élève, bloc) où affecté."""
    rs = []
    for s in inst.students:
        for b, oid in a[s.id_eleve].items():
            if oid:
                o = inst.occ_by_id(oid)
                rs.append(rang(s, o))
    return rs


def distribution_rangs(inst: Instance, a: Assignment) -> pd.Series:
    """Nombre d'affectations obtenues à chaque rang (1 = premier choix)."""
    rs = rangs(inst, a)
    if not rs:
        return pd.Series(dtype=int)
    c = Counter(r + 1 for r in rs)  # 1-indexé pour l'affichage
    return pd.Series(c).sort_index()


def non_affectes(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Une ligne par (élève, bloc) non affecté avec la cause probable."""
    rows = []
    for s in inst.students:
        for b in inst.blocs:
            if a[s.id_eleve][b] is None:
                accs = occ_accessibles(inst, s, b)
                if not accs:
                    cause = "aucune occurrence accessible (créneau/langue/FISEA)"
                elif not s.voeux_par_bloc.get(b):
                    cause = "aucun vœu classé dans ce bloc"
                else:
                    cause = "toutes les occurrences accessibles étaient pleines"
                rows.append({"eleve": s.id_eleve, "bloc": b, "cause": cause})
    return pd.DataFrame(rows)


def remplissage(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Places occupées par occurrence, avec alerte sous l'effectif min."""
    used = Counter()
    for s in inst.students:
        for oid in a[s.id_eleve].values():
            if oid:
                used[oid] += 1
    rows = []
    for o in inst.occurrences:
        n = used[o.id_occ] + o.nb_deja_inscrits
        rows.append({
            "id_occ": o.id_occ, "bloc": o.bloc, "id_ue": o.id_ue,
            "creneau": o.creneau, "periode": o.periode, "langue": o.langue,
            "n_affectes": used[o.id_occ], "total": n, "cap_max": o.cap_max,
            "sous_min": n < o.cap_min, "depasse_max": n > o.cap_max,
        })
    return pd.DataFrame(rows)


def equite_par_groupe(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Rang moyen et taux d'affectation par (régime, langue)."""
    by = defaultdict(list)
    aff = defaultdict(int)
    tot = defaultdict(int)
    for s in inst.students:
        key = (s.regime, s.langue)
        for b, oid in a[s.id_eleve].items():
            tot[key] += 1
            if oid:
                aff[key] += 1
                o = inst.occ_by_id(oid)
                by[key].append(rang(s, o))
    rows = []
    for key in tot:
        rs = by[key]
        rows.append({
            "regime": key[0], "langue": key[1],
            "n_paires": tot[key], "n_affectes": aff[key],
            "taux_aff": aff[key] / tot[key] if tot[key] else 0,
            "rang_moyen": sum(rs) / len(rs) if rs else float("nan"),
            "rang_max": max(rs) if rs else 0,
        })
    return pd.DataFrame(rows)


def resume(inst: Instance, a: Assignment) -> dict:
    """Un dict de résumé prêt à imprimer."""
    rs = rangs(inst, a)
    n_paires = len(inst.students) * len(inst.blocs)
    return {
        "n_paires_totales": n_paires,
        "n_affectations": len(rs),
        "taux_affectation": len(rs) / n_paires if n_paires else 0,
        "rang_moyen": sum(rs) / len(rs) if rs else float("nan"),
        "rang_median": sorted(rs)[len(rs) // 2] if rs else float("nan"),
        "part_1er_choix": sum(1 for r in rs if r == 0) / len(rs) if rs else 0,
        "part_top3": sum(1 for r in rs if r < 3) / len(rs) if rs else 0,
    }


def export_assignment(inst: Instance, a: Assignment, path: str) -> None:
    """CSV lisible : une ligne par affectation (§11.1)."""
    rows = []
    for s in inst.students:
        for b, oid in a[s.id_eleve].items():
            rows.append({"eleveID": s.id_eleve, "bloc": b, "id_occ": oid or ""})
    pd.DataFrame(rows).to_csv(path, sep=";", index=False)
