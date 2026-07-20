"""Pipeline complet — de deux CSV Synapse à un CSV import + rapports.

Étapes :
    1. Chargement (data.loaders.build_campaign)
    2. Priorités (solvers.PriorityChain)
    3. Optimisation (solvers.MipSolver, ou tout autre Solver)
    4. Export Synapse + rapports (reporting)

Exposé aussi en CLI :

    python -m src.pipeline data/samples/etudiants_anonymises.csv \\
                           data/samples/campagne_synthetique.csv \\
                           --out out/
"""
from __future__ import annotations
import argparse
import time
from pathlib import Path
from .data import build_campaign
from .data.model import Campaign, Assignment
from .solvers import PriorityChain, MipSolver, Solver
from .reporting import Report, export_synapse_import


def run_campaign(students_csv: str | Path, campaign_csv: str | Path,
                 ecue_csv: str | Path | None = None,
                 solver: Solver | None = None,
                 out_dir: str | Path = "out") -> tuple[Campaign, Assignment, Report]:
    """Charge, résout, écrit — renvoie campagne, affectation, rapport."""
    campaign = build_campaign(students_csv, campaign_csv, ecue_csv)
    solver = solver or MipSolver()
    pre = PriorityChain().apply(campaign)
    assignment = solver.solve(campaign, pre_assignment=pre)
    report = Report(campaign, assignment)

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    export_synapse_import(campaign, assignment, out / "synapse_import.csv")
    report.not_assigned().to_csv(out / "not_assigned.csv", sep=";", index=False)
    report.filling().to_csv(out / "filling.csv", sep=";", index=False)
    report.stats_per_demande().to_csv(out / "stats_per_demande.csv", sep=";", index=False)
    report.stats_compensation().to_csv(out / "stats_compensation.csv", sep=";", index=False)
    return campaign, assignment, report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("students_csv")
    p.add_argument("campaign_csv")
    p.add_argument("--ecue", default=None, help="fichier ECUE (défaut : embarqué)")
    p.add_argument("--out", default="out", help="dossier de sortie")
    p.add_argument("--time-limit", type=float, default=60.0)
    args = p.parse_args()

    t0 = time.time()
    _, assignment, report = run_campaign(
        args.students_csv, args.campaign_csv, args.ecue,
        solver=MipSolver(time_limit_s=args.time_limit), out_dir=args.out,
    )
    dt = time.time() - t0
    n_ok = sum(1 for v in assignment.values() if v)
    stats = report.stats_global()
    print(f"Terminé en {dt:.1f}s")
    print(f"  Affectations : {n_ok}/{stats['n_expected']} "
          f"({stats['assignment_rate']*100:.1f}%)")
    print(f"  Premier choix : {stats['first_choice_share']*100:.1f}%")
    print(f"  Top-3        : {stats['top3_share']*100:.1f}%")
    print(f"  Sorties dans {args.out}/")


if __name__ == "__main__":
    main()
