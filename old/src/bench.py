"""Bench comparatif de tous les algorithmes.

Usage :
    python -m src.bench --data data/           # tous les algos
    python -m src.bench --data data/ --algo flow  # un seul

Écrit un CSV par algo + un rapport ``docs/resultats.md``.
"""
from __future__ import annotations
import argparse, time
from pathlib import Path
import pandas as pd
from .preprocess import load
from .report import (resume, distribution_rangs, remplissage,
                    equite_par_groupe, export_assignment,
                    non_affectes, satisfaction_par_eleve)
from . import feasibility
from . import (algo_rsd, algo_flow, algo_mip, algo_hungarian, algo_da,
               algo_equite, algo_mip_full)
from . import verif_contraintes

ALGOS = {a.NAME: a for a in (algo_rsd, algo_flow, algo_mip, algo_hungarian,
                              algo_da, algo_equite, algo_mip_full)}


def run(inst, algo_name: str) -> tuple[dict, dict, float]:
    algo = ALGOS[algo_name]
    t0 = time.time()
    a = algo.solve(inst)
    dt = time.time() - t0
    return a, resume(inst, a), dt


def _pct(x: float) -> str:
    return f"{x*100:.1f}%"


def bench(data_dir: str, out_dir: str, only: str | None = None) -> None:
    inst = load(data_dir)
    out = Path(out_dir)
    out.mkdir(exist_ok=True, parents=True)
    print(f"Instance : {len(inst.students)} élèves, {len(inst.occurrences)} occ, {len(inst.blocs)} blocs")

    # Analyse de faisabilité en amont (explicabilité).
    feas = feasibility.resume(inst)
    print("\nFaisabilité (avant tout algo) :")
    for k, v in feas.items():
        print(f"  {k}: {v}")
    feasibility.par_eleve(inst).to_csv(out / "feas_par_eleve.csv", sep=";", index=False)
    feasibility.par_occurrence(inst).to_csv(out / "feas_par_occurrence.csv", sep=";", index=False)
    feasibility.impossibles(inst).to_csv(out / "feas_impossibles.csv", sep=";", index=False)

    algos = [only] if only else list(ALGOS)
    resumes, dists = [], {}
    for name in algos:
        print(f"\n== {name} ==")
        a, r, dt = run(inst, name)
        r["algo"] = name
        r["temps_s"] = dt
        resumes.append(r)
        dists[name] = distribution_rangs(inst, a)
        print(f"  temps: {dt:.1f}s  aff: {_pct(r['taux_affectation'])}  "
              f"rang_moyen: {r['rang_moyen']:.2f}  1er choix: {_pct(r['part_1er_choix'])}")
        export_assignment(inst, a, out / f"assignment_{name}.csv")
        remplissage(inst, a).to_csv(out / f"remplissage_{name}.csv", sep=";", index=False)
        equite_par_groupe(inst, a).to_csv(out / f"equite_{name}.csv", sep=";", index=False)
        non_affectes(inst, a).to_csv(out / f"non_affectes_{name}.csv", sep=";", index=False)
        satisfaction_par_eleve(inst, a).to_csv(out / f"satisfaction_{name}.csv", sep=";", index=False)
        v = verif_contraintes.verifier(inst, a)["resume"]
        r["violations"] = v["total_violations"]
        print(f"  contraintes : " + " ".join(f"{k}={v[k]}" for k in
              ("accessibilite", "exclusion_instant", "unicite_ecue",
               "capacite", "completude", "charge")))

    df = pd.DataFrame(resumes)
    df = df[["algo", "temps_s", "taux_affectation", "rang_moyen", "rang_median",
             "rang_q75", "rang_d9", "rang_max",
             "part_1er_choix", "part_top3", "part_rang_gte_5",
             "n_affectations", "violations"]]
    df.to_csv(out / "bench_summary.csv", sep=";", index=False)
    _write_report(inst, df, Path("docs/resultats.md"), dists, feas)
    print(f"\nBench terminé. Résultats dans {out}/ et docs/resultats.md")


def _write_report(inst, df, path: Path, dists, feas: dict) -> None:
    lines = [
        "# Résultats comparatifs des algorithmes",
        "",
        f"Instance : **{len(inst.students)} élèves**, **{len(inst.occurrences)} occurrences**, "
        f"**{len(inst.blocs)} blocs**.",
        "",
        "## Analyse de faisabilité (avant tout algorithme)",
        "",
        "Ces chiffres décrivent ce que la structure des contraintes autorise, indépendamment de"
        " tout algorithme. Ils fournissent la borne supérieure du taux d'affectation.",
        "",
        f"- Paires (élève, bloc) totales : **{feas['n_paires_eleve_bloc']}**",
        f"- Paires **structurellement impossibles** (aucune occurrence accessible) : "
        f"**{feas['paires_sans_occurrence_accessible']}** — voir `out/feas_impossibles.csv`",
        f"- Paires sans vœu classé : {feas['paires_sans_voeu_classe']}",
        f"- Paires dont les vœux tombent hors des occurrences accessibles : "
        f"{feas['paires_voeux_hors_atteinte']}",
        f"- Occurrences tendues (demande > capacité) : "
        f"**{feas['occurrences_tendues_gt_100pct']}** — voir `out/feas_par_occurrence.csv`",
        "",
        "## Tableau récapitulatif",
        "",
        "| Algo | Temps (s) | Taux aff. | Rang moy | Méd. | Q75 | D9 | Max | 1er | Top-3 | ≥5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| **{r['algo']}** | {r['temps_s']:.1f} | {_pct(r['taux_affectation'])} | "
            f"{r['rang_moyen']:.2f} | {r['rang_median']:.0f} | {r['rang_q75']:.0f} | "
            f"{r['rang_d9']:.0f} | {int(r['rang_max'])} | "
            f"{_pct(r['part_1er_choix'])} | {_pct(r['part_top3'])} | "
            f"{_pct(r['part_rang_gte_5'])} |")
    lines += ["",
              "*Rangs 1-indexés partout : `1` = premier choix. « Méd » = médiane, "
              "« Q75 » = troisième quartile, « D9 » = neuvième décile, « ≥5 » = part "
              "d'affectations avec rang ≥ 5 (élèves mal servis).*",
              "",
              "## Distribution des rangs obtenus",
              "",
              "| Algo | 1 | 2 | 3 | 4 | 5 | 6 | ≥7 | non affecté |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    total_paires = feas["n_paires_eleve_bloc"]
    for name in df["algo"]:
        d = dists[name]
        vals = [int(d.get(k, 0)) for k in range(1, 7)]
        rest = int(d[d.index >= 7].sum())
        na = total_paires - int(d.sum())
        lines.append(f"| **{name}** | " + " | ".join(map(str, vals + [rest, na])) + " |")

    lines += ["",
              "## Fichiers produits (dossier `out/`)",
              "",
              "**Faisabilité** (une seule fois par instance) :",
              "- `feas_par_eleve.csv` — pour chaque paire (élève, bloc) : nb accessibles, nb vœux atteignables.",
              "- `feas_par_occurrence.csv` — demande théorique vs capacité, cours tendus en tête.",
              "- `feas_impossibles.csv` — paires structurellement bloquées.",
              "",
              "**Par algo** :",
              "- `assignment_<algo>.csv` — affectations (§11.1).",
              "- `remplissage_<algo>.csv` — occupation par occurrence, alertes sous/dépassement.",
              "- `equite_<algo>.csv` — rang moyen par (régime, langue).",
              "- `non_affectes_<algo>.csv` — liste **nominative** avec cause.",
              "- `satisfaction_<algo>.csv` — rangs par bloc, somme, pire bloc.",
              ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data", help="dossier des CSV d'entrée")
    p.add_argument("--out", default="out", help="dossier des sorties")
    p.add_argument("--algo", default=None, choices=list(ALGOS), help="un seul algo")
    args = p.parse_args()
    bench(args.data, args.out, args.algo)


if __name__ == "__main__":
    main()
