"""Analyse structurelle des profils d'élève × blocs.

Sortie : tableaux (créneaux libres par profil, occurrences accessibles par
(profil, bloc), capacité maximale accessible par bloc) — utilisés dans
``docs/limites_structurelles.md``. Aucune référence aux vœux réels : on ne
regarde que la STRUCTURE (créneaux, langues, FISEA, jours d'entreprise).

Usage : python -m tools.analyse_structurelle data/2026
"""
from __future__ import annotations
import sys
from pathlib import Path
from itertools import combinations
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.preprocess import load
from src.constantes import (CRENEAUX, JOURS, CRENEAUX_GROUPES,
                             JOUR_DU_CRENEAU, jours_entreprise_apprenti)


def _libres(groupes: list[str], periode: int, regime: str) -> set[str]:
    """Créneaux disponibles pour un profil (indépendamment du bloc et de la langue)."""
    occupes = set().union(*(CRENEAUX_GROUPES[g][periode] for g in groupes)) if groupes else set()
    entreprise = (jours_entreprise_apprenti(groupes[0], periode)
                  if regime == "apprenti" and groupes else set())
    return {c for c in CRENEAUX
            if c not in occupes and JOUR_DU_CRENEAU[c] not in entreprise}


def _profils() -> list[dict]:
    """Enumère tous les profils structurels raisonnables."""
    out = []
    # Étudiants classiques : deux filières parmi {A, B, C}
    for combo in combinations(("A", "B", "C"), 2):
        for langue in ("FR", "EN"):
            out.append({"nom": f"Étudiant {'+'.join(combo)} {langue}",
                        "regime": "etudiant", "groupes": list(combo), "langue": langue})
    # Apprentis : une seule filière
    for g in ("A", "B", "C"):
        for langue in ("FR", "EN"):
            out.append({"nom": f"Apprenti {g} {langue}",
                        "regime": "apprenti", "groupes": [g], "langue": langue})
    # Auditeurs (échange) : aucune filière
    for langue in ("FR", "EN"):
        out.append({"nom": f"Auditeur {langue}",
                    "regime": "auditeur", "groupes": [], "langue": langue})
    return out


def creneaux_par_profil() -> pd.DataFrame:
    """Créneaux libres de chaque profil, par semestre."""
    rows = []
    for p in _profils():
        for periode, sem in [(1, "S1"), (3, "S2")]:
            libres = sorted(_libres(p["groupes"], periode, p["regime"]))
            rows.append({"profil": p["nom"], "semestre": sem,
                         "n_creneaux_libres": len(libres),
                         "creneaux_libres": " ".join(libres)})
    return pd.DataFrame(rows)


def _accessible(occ, profil) -> bool:
    """Une occurrence est-elle accessible à ce profil ?"""
    if not occ.creneau or occ.periode == 0:
        return False
    if occ.fisea and profil["regime"] != "apprenti":
        return False
    libres = _libres(profil["groupes"], occ.periode, profil["regime"])
    if occ.creneau not in libres:
        return False
    if profil["langue"] == "EN" and occ.periode in (1, 2) and occ.langue == "FR":
        return False
    return True


def accessibilite_par_profil_bloc(inst) -> pd.DataFrame:
    """Une ligne par (profil, bloc) : nb occurrences accessibles + capacité totale."""
    rows = []
    for p in _profils():
        for bloc in inst.blocs:
            accs = [o for o in inst.occ_by_bloc(bloc) if _accessible(o, p)]
            rows.append({
                "profil": p["nom"], "bloc": bloc,
                "n_occurrences": len(accs),
                "capacite_totale": sum(o.cap_dispo for o in accs),
                "accessible": "OK" if accs else "BLOQUÉ",
            })
    return pd.DataFrame(rows)


def matrice_profil_bloc(inst) -> pd.DataFrame:
    """Pivot lisible : profils en lignes, blocs en colonnes, `n_occ (cap)` en cellule."""
    df = accessibilite_par_profil_bloc(inst)
    df["cell"] = df.apply(
        lambda r: f"{int(r['n_occurrences'])} ({int(r['capacite_totale'])})"
                  if r['n_occurrences'] > 0 else "**BLOQUÉ**", axis=1)
    return df.pivot(index="profil", columns="bloc", values="cell")


def blocs_accessibles_max(inst) -> pd.DataFrame:
    """Nombre de blocs sur lesquels le profil peut recevoir au moins une affectation."""
    rows = []
    for p in _profils():
        n = sum(1 for bloc in inst.blocs
                if any(_accessible(o, p) for o in inst.occ_by_bloc(bloc)))
        rows.append({"profil": p["nom"], "blocs_accessibles": n,
                     "credits_max_theoriques": round(n * 2.5, 1),
                     "cible_15_credits": "OK" if n >= 6 else "SOUS-CHARGE"})
    return pd.DataFrame(rows)


def capacite_totale_par_bloc(inst) -> pd.DataFrame:
    """Structurel : capacité totale d'un bloc vs taille promo (348 en 2026)."""
    n_etu = len(inst.students) if inst.students else 348
    rows = []
    for bloc in inst.blocs:
        occs = inst.occ_by_bloc(bloc)
        cap_totale = sum(o.cap_dispo for o in occs)
        cap_non_fisea = sum(o.cap_dispo for o in occs if not o.fisea)
        rows.append({"bloc": bloc, "n_occurrences": len(occs),
                     "capacite_totale": cap_totale,
                     "capacite_hors_fisea": cap_non_fisea,
                     "n_etudiants_promo": n_etu,
                     "surplus_hors_fisea": cap_non_fisea - n_etu,
                     "saturable": "TENDU" if cap_non_fisea < n_etu else "OK"})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else "data/2026"
    inst = load(data)
    print(f"# Analyse structurelle sur {data}\n")
    print("## Créneaux libres par profil\n")
    print(creneaux_par_profil().to_string(index=False))
    print("\n## Matrice profil × bloc (n_occurrences (capacité))\n")
    print(matrice_profil_bloc(inst).to_string())
    print("\n## Blocs accessibles maximum par profil\n")
    print(blocs_accessibles_max(inst).to_string(index=False))
    print("\n## Capacité par bloc vs taille promo\n")
    print(capacite_totale_par_bloc(inst).to_string(index=False))
