"""Bench isolé de l'approche A-CEEI expérimentale.

Usage :
    python experiments/bench_aceei.py [data_dir]

Rendu de résultat séparé du bench principal (`python -m src.bench`), car
`fairpyx` est plus lent et n'a pas les mêmes garanties que les autres
approches. On le garde ici pour comparaison, pas comme candidat de prod.
"""
from __future__ import annotations
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.preprocess import load
from src.report import resume, distribution_rangs
from experiments import algo_aceei

def main(data_dir: str = "data") -> None:
    inst = load(data_dir)
    print(f"Instance : {len(inst.students)} eleves, {len(inst.occurrences)} occ, "
          f"{len(inst.blocs)} blocs")
    t0 = time.time()
    a = algo_aceei.solve(inst)
    dt = time.time() - t0
    r = resume(inst, a)
    print(f"\naceei en {dt:.1f}s :")
    for k, v in r.items():
        print(f"  {k}: {v}")
    print("\nDistribution des rangs (1..10) :")
    print(distribution_rangs(inst, a).head(10).to_string())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
