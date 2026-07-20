"""Bench multi-seed pour les algorithmes stochastiques.

Certains algorithmes utilisent une source aléatoire (RSD, DA, Upgrade,
Water Filling, Equite — via son shuffle interne). Ce script les exécute
K fois avec des seeds différents et rapporte moyenne/écart-type des
métriques clés. Les algorithmes déterministes (Flow, MIP, Hungarian) sont
exécutés une seule fois.

Usage :
    python -m tools.bench_multi data/            # 10 seeds par défaut
    python -m tools.bench_multi data/ --seeds 20
"""
from __future__ import annotations
import argparse, statistics, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.preprocess import load
from src.report import resume, satisfaction_par_eleve
from src import algo_rsd, algo_flow, algo_mip, algo_hungarian, algo_da, algo_equite
from experiments import algo_upgrade, algo_waterfilling

DETERMINISTES = {"flow": algo_flow, "mip": algo_mip, "hungarian": algo_hungarian}
STOCHASTIQUES = {"rsd": algo_rsd, "da": algo_da, "equite": algo_equite,
                 "upgrade": algo_upgrade, "waterfilling": algo_waterfilling}


def _stats(vals: list[float]) -> tuple[float, float]:
    if len(vals) <= 1:
        return (vals[0] if vals else 0.0, 0.0)
    return (statistics.mean(vals), statistics.stdev(vals))


def _run(inst, algo, seed: int | None) -> dict:
    t0 = time.time()
    a = algo.solve(inst, seed=seed) if seed is not None else algo.solve(inst)
    dt = time.time() - t0
    r = resume(inst, a)
    sat = satisfaction_par_eleve(inst, a)
    return {"aff": r["n_affectations"], "r_moy": r["rang_moyen"],
            "first": r["part_1er_choix"] * 100, "top3": r["part_top3"] * 100,
            "ge5": r["part_rang_gte_5"] * 100,
            "pire_moy": float(sat["pire_rang"].mean()),
            "pire_max": int(sat["pire_rang"].max()), "t": dt}


def bench(data_dir: str, seeds: int = 10) -> None:
    inst = load(data_dir)
    print(f"Instance : {len(inst.students)} élèves, {len(inst.blocs)} blocs, {seeds} seeds\n")
    print(f"{'algo':<14} {'aff':>10} {'r_moy':>12} {'1er%':>12} {'top3%':>12} {'>=5%':>12} {'pire_moy':>12} {'pire_max':>10} {'t(s)':>8}")

    for name, mod in DETERMINISTES.items():
        m = _run(inst, mod, None)
        print(f"{name:<14} {int(m['aff']):>10} {m['r_moy']:>12.2f} "
              f"{m['first']:>12.1f} {m['top3']:>12.1f} {m['ge5']:>12.1f} "
              f"{m['pire_moy']:>12.2f} {m['pire_max']:>10} {m['t']:>8.1f}")

    for name, mod in STOCHASTIQUES.items():
        runs = [_run(inst, mod, s) for s in range(seeds)]
        agg = {k: _stats([r[k] for r in runs]) for k in
               ("aff", "r_moy", "first", "top3", "ge5", "pire_moy", "pire_max", "t")}
        f = lambda k, d=2: f"{agg[k][0]:.{d}f}±{agg[k][1]:.{d}f}"
        print(f"{name:<14} {f('aff', 0):>10} {f('r_moy'):>12} "
              f"{f('first', 1):>12} {f('top3', 1):>12} {f('ge5', 1):>12} "
              f"{f('pire_moy'):>12} {f('pire_max', 1):>10} {f('t', 1):>8}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("data", nargs="?", default="data")
    p.add_argument("--seeds", type=int, default=10)
    a = p.parse_args()
    bench(a.data, a.seeds)


if __name__ == "__main__":
    main()
