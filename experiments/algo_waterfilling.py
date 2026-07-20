"""Approche 2 : water filling — tout le monde au pire rang, puis promotions.

Idée utilisateur (interprétation raisonnable) :
  1. Chaque élève est initialement placé au **pire rang** accessible de chacun
     de ses blocs (« au fond du bloc »).
  2. Tour à tour, en ordre aléatoire, on tente de **promouvoir** chaque élève
     d'un cran vers le haut de ses vœux — si l'occurrence cible a de la place
     et que la promotion améliore effectivement le rang.
  3. L'ordre est **rotatif** entre passes : ceux servis en dernier au tour k
     deviennent premiers au tour k+1. Cela crée une compensation naturelle.
  4. Convergence lorsque plus aucune promotion n'est possible.

Contrairement à :class:`algo_upgrade`, ici on ne fait pas de swaps entre
élèves — juste des « glissements » vers le haut si la place est libre.
Analogie : chaque bloc est un tuyau capacité ; l'eau (les élèves) monte des
niveaux bas (pire rang) vers les niveaux hauts (meilleur rang) tant que le
niveau supérieur n'est pas plein.
"""
from __future__ import annotations
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.model import Instance, Assignment
from src.common import empty_assignment, rang, reste_capacite
from src.filters import occ_accessibles

NAME = "waterfilling"


def solve(inst: Instance, seed: int = 0, max_passes: int = 40) -> Assignment:
    a = _init_pire_rang(inst)
    order = list(inst.students)
    rng = random.Random(seed)
    for i in range(max_passes):
        rng.shuffle(order)
        if not _promote_pass(inst, a, order):
            break
    return a


def _init_pire_rang(inst: Instance) -> Assignment:
    """Chaque élève placé au pire rang accessible de chacun de ses blocs.

    On respecte la capacité : si le pire est plein, on tente l'avant-pire, etc.
    Sinon on laisse non-affecté (cas structurellement impossible).
    """
    reste = {o.id_occ: o.cap_dispo for o in inst.occurrences}
    result = empty_assignment(inst)
    # Ordre : blocs traités en séquence, élèves triés par nb vœux croissant
    # (les plus contraints d'abord).
    for bloc in inst.blocs:
        cands = [s for s in inst.students if s.voeux_par_bloc.get(bloc)]
        cands.sort(key=lambda s: len(occ_accessibles(inst, s, bloc)))
        for s in cands:
            accs = sorted(occ_accessibles(inst, s, bloc),
                          key=lambda o: -rang(s, o))  # pire rang d'abord
            for o in accs:
                if reste[o.id_occ] > 0:
                    result[s.id_eleve][bloc] = o.id_occ
                    reste[o.id_occ] -= 1
                    break
    return result


def _promote_pass(inst: Instance, a: Assignment, order: list) -> bool:
    """Un tour de promotions. Renvoie True si au moins une promotion a eu lieu."""
    occ = {o.id_occ: o for o in inst.occurrences}
    reste = reste_capacite(inst, a)
    improved = False
    for s in order:
        for bloc in inst.blocs:
            oid = a[s.id_eleve][bloc]
            if oid is None:
                continue
            r_now = rang(s, occ[oid]) + 1
            if r_now == 1:
                continue
            # Chercher une occurrence mieux classée avec de la place.
            for o in sorted(occ_accessibles(inst, s, bloc), key=lambda o: rang(s, o)):
                if rang(s, o) + 1 >= r_now:
                    break
                if reste[o.id_occ] > 0:
                    reste[oid] += 1
                    reste[o.id_occ] -= 1
                    a[s.id_eleve][bloc] = o.id_occ
                    improved = True
                    break
    return improved


