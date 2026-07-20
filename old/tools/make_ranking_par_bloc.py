"""Dérive ``eleves_par_bloc.csv`` depuis ``eleves.csv``.

Format de sortie (une ligne par (élève, bloc)) :

    eleveID ; filiere ; info ; bloc ; classement

Le champ ``classement`` est la liste des codes UE du bloc, dans l'ordre où
ils apparaissent dans le classement global de l'élève, séparés par ``|``.

Usage :
    python -m tools.make_ranking_par_bloc data/
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd


def main(data_dir: str = "data") -> None:
    d = Path(data_dir)
    eleves = pd.read_csv(d / "eleves.csv", sep=";")
    cours = pd.read_csv(d / "cours.csv", sep=";")

    ue_to_bloc = dict(zip(cours["Code UE"].str.strip(), cours["Type ens."].str.strip()))
    blocs = sorted(set(ue_to_bloc.values()))

    rows = []
    for _, r in eleves.iterrows():
        classement = [c.strip() for c in str(r["classement_matieres"]).split("|")]
        for bloc in blocs:
            projete = [ue for ue in classement if ue_to_bloc.get(ue) == bloc]
            rows.append({
                "eleveID": r["eleveID"], "filiere": r["filiere"], "info": r.get("info", ""),
                "bloc": bloc, "classement": "|".join(projete),
            })

    out = d / "eleves_par_bloc.csv"
    pd.DataFrame(rows).to_csv(out, sep=";", index=False)
    print(f"{out} ecrit ({len(rows)} lignes)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
