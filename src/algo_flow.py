"""Min-cost flow par bloc (§13.2). Exact et rapide.

Chaque bloc est un réseau indépendant :

    src --1,0--> eleve --1,cout--> occurrence --cap,0--> puits
              \\                                        /
                +--------- BIG_M, 1 --------- puits ---+  (option "non-affecté")

L'arc « fallback » eleve→puits garantit la faisabilité (un élève sans place
possible paie un coût énorme mais n'échoue pas).
"""
from __future__ import annotations
import networkx as nx
from .model import Instance, Assignment
from .common import couts_accessibles, empty_assignment
from .constantes import BIG_M

NAME = "flow"


def solve(inst: Instance) -> Assignment:
    result = empty_assignment(inst)
    for bloc in inst.blocs:
        _solve_bloc(inst, bloc, result)
    return result


def _solve_bloc(inst: Instance, bloc: str, result: Assignment) -> None:
    G = nx.DiGraph()
    G.add_node("src", demand=-len(inst.students))
    G.add_node("puits", demand=len(inst.students))

    for o in inst.occ_by_bloc(bloc):
        if o.cap_dispo > 0:
            G.add_edge(f"O:{o.id_occ}", "puits", capacity=o.cap_dispo, weight=0)

    for s in inst.students:
        e = f"E:{s.id_eleve}"
        G.add_edge("src", e, capacity=1, weight=0)
        G.add_edge(e, "puits", capacity=1, weight=BIG_M)  # non-affecté
        for o, c in couts_accessibles(inst, s, bloc):
            if o.cap_dispo > 0:
                G.add_edge(e, f"O:{o.id_occ}", capacity=1, weight=int(c))

    flow = nx.min_cost_flow(G)
    for s in inst.students:
        for dest, val in flow[f"E:{s.id_eleve}"].items():
            if val == 1 and dest.startswith("O:"):
                result[s.id_eleve][bloc] = dest[2:]
                break
