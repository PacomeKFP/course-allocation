# Documentation des six approches

Chaque approche vit dans un unique fichier `src/algo_*.py` de moins de 100
lignes. Elles exposent toutes la même signature :

```python
def solve(instance: Instance) -> Assignment
```

où `Assignment = dict[eleveID -> dict[bloc -> id_occ|None]]`.

Le calcul du **coût** (helper `src/common.py`) est partagé :

```
coût(élève, occurrence) = rang_dans_les_vœux + pénalité_si_non_classé
                        − BONUS_ANGLOPHONE  si (élève anglo ET cours en anglais)
```

Voir [`cahier_des_charges.md`](cahier_des_charges.md) §13 pour la référence
académique. Voir [`resultats.md`](resultats.md) pour les chiffres.

---

## 1. `algo_rsd.py` — Random Serial Dictator

**Idée.** On tire un ordre aléatoire des élèves. Chacun, à son tour, prend son
meilleur vœu accessible encore disponible dans chaque bloc.

**Complexité.** Linéaire, quelques millisecondes sur 340 élèves × 9 blocs.

**Force.** Simplicité extrême (≈ 30 lignes) et robustesse à la déclaration.

**Faiblesse.** Les derniers servis peuvent n'avoir rien qui leur reste — d'où
un taux d'affectation moindre.

## 2. `algo_flow.py` — Min-cost flow par bloc

**Idée (§13.2).** Pour chaque bloc, un réseau bipartite avec source, élèves,
occurrences et puits. Le coût d'un arc élève→occurrence est le rang du vœu,
avec bonus anglophone. Un arc de secours élève→puits à coût prohibitif
garantit la faisabilité même si l'élève n'a aucun cours accessible.

**Lib.** `networkx.min_cost_flow`.

**Force.** Exact et rapide (< 1 s), sortie facile à déboguer arc par arc.

**Limite.** Traite chaque bloc indépendamment ; ne modélise pas le couplage
inter-blocs (charge par période, unicité UE inter-blocs).

## 3. `algo_mip.py` — MIP global (OR-Tools CP-SAT)

**Idée (§13.1).** Une seule variable binaire `x[élève, occurrence]` pour
chaque paire accessible. Contraintes : au plus une occurrence par (élève, bloc),
capacité par occurrence. Slack `u[élève, bloc]` avec coût prohibitif absorbe
les non-affectations. Objectif : minimiser la somme des coûts + pénalités.

**Lib.** `ortools.sat.python.cp_model`.

**Force.** Cadre le plus flexible : toute contrainte souple (charge par
période, priorité redoublants…) s'ajoute en une ligne. Résout globalement.

**Coût.** Un peu plus lent (~ 5 s) — plus lourd que le flow pour ce problème.

## 4. `algo_hungarian.py` — Algorithme hongrois

**Idée (§13.3).** L'algo hongrois traite l'appariement un-à-un. Pour supporter
les capacités > 1, on **duplique** chaque occurrence *c* fois. Matrice
carrée obtenue par ajout de colonnes fictives à coût prohibitif.

**Lib.** `scipy.optimize.linear_sum_assignment`.

**Force.** Exact, très rapide sur matrices de quelques centaines.

**Limite.** Ne passe pas à l'échelle si les capacités deviennent très grandes
(matrice explose). Aucun couplage inter-blocs.

## 5. `algo_da.py` — Deferred Acceptance (Gale-Shapley)

**Idée (§13.4).** Chaque élève « propose » son meilleur vœu ; chaque
occurrence accepte provisoirement les meilleurs candidats selon sa capacité
et une priorité (ici anglophone d'abord sur cours en anglais), rejette les
autres, qui proposent leur choix suivant.

**Lib.** `matching.games.HospitalResident`.

**Force.** Robuste à la déclaration (déclarer ses vrais vœux est optimal
pour l'élève). La priorité anglophone s'encode naturellement dans l'ordre de
préférence côté occurrence.

**Limite.** Ne cherche pas l'optimum global de bien-être ; produit un
matching stable, pas nécessairement le plus efficace.

## 6. `algo_aceei.py` — Allocation équitable (fairpyx)

**Idée (§13.5, adaptée).** Fairpyx ne fournit pas A-CEEI/Course-Match
directement. On utilise `iterated_maximum_matching_adjusted` qui itère des
couplages maximums pondérés avec correction d'équité entre agents.

**Lib.** `fairpyx`.

**Modélisation.**
- utilité(élève, occurrence) = 100 − 5×rang (positive, plus grand = mieux) ;
- `agent_conflicts` élimine les paires inaccessibles ;
- `item_conflicts` : dans un même bloc, les occurrences sont mutuellement
  exclusives.

**Force.** Cible l'**équité** ; le tableau des rangs (`resultats.md`)
montre qu'aceei donne plus souvent le **premier** choix (~63 %) que les
approches utilitaires.

**Limite.** Modèle très différent des autres approches ; plus lent ; le
proxy retenu n'a pas toutes les propriétés d'A-CEEI. Cf. `notes.md` N16.
