"""Vérification post-affectation de la charge de chaque élève.

Règle : chaque bloc affecté = 1 période occupée = **2,5 crédits**. La cible
institutionnelle est **≥ 15 crédits (soit 6 blocs)**, l'idéal étant 8.

Le script recoupe l'affectation avec l'analyse structurelle : un élève
en sous-charge peut l'être soit parce que l'algo l'a mal servi, soit
parce que son profil ne lui donne PAS accès à 6 blocs (cas apprenti A).
Ce recoupement évite de blâmer l'algorithme quand le blocage est structurel.
"""
from __future__ import annotations
import pandas as pd
from .model import Instance, Assignment
from .filters import occ_accessibles

CREDITS_PAR_BLOC = 2.5
CIBLE_BLOCS = 6
IDEAL_BLOCS = 8


def charge_par_eleve(inst: Instance, a: Assignment) -> pd.DataFrame:
    """Une ligne par élève : blocs obtenus, blocs accessibles théoriquement, crédits."""
    rows = []
    for s in inst.students:
        n_obtenus = sum(1 for oid in a[s.id_eleve].values() if oid)
        n_accessibles = sum(1 for b in inst.blocs if occ_accessibles(inst, s, b))
        credits = round(n_obtenus * CREDITS_PAR_BLOC, 1)
        blocage_structurel = n_accessibles < CIBLE_BLOCS
        rows.append({
            "eleve": s.id_eleve, "regime": s.regime, "langue": s.langue,
            "groupes": "+".join(s.groupes_filiere) or "-",
            "n_blocs_obtenus": n_obtenus,
            "n_blocs_accessibles_theo": n_accessibles,
            "credits": credits,
            "atteint_cible_15cr": credits >= 15,
            "atteint_ideal_20cr": credits >= 20,
            "sous_charge_structurelle": blocage_structurel,
        })
    return pd.DataFrame(rows)


def resume_charge(inst: Instance, a: Assignment) -> dict:
    df = charge_par_eleve(inst, a)
    return {
        "n_eleves": len(df),
        "credits_moyens": round(df["credits"].mean(), 1),
        "credits_median": float(df["credits"].median()),
        "credits_min": float(df["credits"].min()),
        "n_eleves_15cr_ok": int(df["atteint_cible_15cr"].sum()),
        "n_eleves_20cr_ok": int(df["atteint_ideal_20cr"].sum()),
        "n_eleves_sous_cible": int((~df["atteint_cible_15cr"]).sum()),
        "n_eleves_sous_charge_structurelle": int(df["sous_charge_structurelle"].sum()),
        "n_eleves_sous_cible_hors_structurel": int(
            (~df["atteint_cible_15cr"] & ~df["sous_charge_structurelle"]).sum()),
    }


def _fmt(v):
    return f"{v:.1f}" if isinstance(v, float) else str(v)


def print_rapport(inst: Instance, a: Assignment) -> None:
    """Petit rapport en console."""
    r = resume_charge(inst, a)
    df = charge_par_eleve(inst, a)
    print("Charge par élève (rappel : 1 bloc = 2,5 crédits, cible = 15)")
    for k, v in r.items():
        print(f"  {k}: {_fmt(v)}")
    print(f"\nRépartition des blocs obtenus :")
    print(df["n_blocs_obtenus"].value_counts().sort_index().to_string())
    sous = df[~df["atteint_cible_15cr"] & ~df["sous_charge_structurelle"]]
    if len(sous):
        print(f"\n{len(sous)} élèves sous la cible pour cause d'algo (à corriger) :")
        print(sous.head(20).to_string(index=False))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.preprocess import load
    from src.algo_equite import solve
    inst = load(sys.argv[1] if len(sys.argv) > 1 else "data")
    a = solve(inst)
    print_rapport(inst, a)
