# Résultats comparatifs des algorithmes

Instance : **340 élèves**, **67 occurrences**, **9 blocs**.

## Analyse de faisabilité (avant tout algorithme)

Ces chiffres décrivent ce que la structure des contraintes autorise, indépendamment de tout algorithme. Ils fournissent la borne supérieure du taux d'affectation.

- Paires (élève, bloc) totales : **3060**
- Paires **structurellement impossibles** (aucune occurrence accessible) : **60** — voir `out/feas_impossibles.csv`
- Paires sans vœu classé : 0
- Paires dont les vœux tombent hors des occurrences accessibles : 60
- Occurrences tendues (demande > capacité) : **63** — voir `out/feas_par_occurrence.csv`

## Tableau récapitulatif

| Algo | Temps (s) | Taux aff. | Rang moy | Méd. | Q75 | D9 | Max | 1er | Top-3 | ≥5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **rsd** | 0.0 | 89.4% | 1.86 | 1 | 2 | 3 | 10 | 58.2% | 91.0% | 5.1% |
| **flow** | 0.8 | 95.7% | 1.75 | 1 | 2 | 3 | 10 | 57.6% | 92.9% | 4.2% |
| **mip** | 2.9 | 95.7% | 1.74 | 1 | 2 | 3 | 10 | 57.4% | 93.1% | 4.2% |
| **hungarian** | 1.9 | 95.7% | 1.75 | 1 | 2 | 3 | 10 | 57.7% | 92.9% | 4.3% |
| **da** | 1.0 | 90.6% | 1.84 | 1 | 2 | 3 | 12 | 58.0% | 91.3% | 4.8% |
| **equite** | 3.4 | 95.7% | 1.74 | 1 | 2 | 3 | 9 | 56.5% | 92.9% | 4.3% |
| **mip_full** | 7.3 | 93.4% | 1.80 | 1 | 2 | 3 | 12 | 56.6% | 92.5% | 4.3% |

*Rangs 1-indexés partout : `1` = premier choix. « Méd » = médiane, « Q75 » = troisième quartile, « D9 » = neuvième décile, « ≥5 » = part d'affectations avec rang ≥ 5 (élèves mal servis).*

## Distribution des rangs obtenus

| Algo | 1 | 2 | 3 | 4 | 5 | 6 | ≥7 | non affecté |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **rsd** | 1591 | 669 | 229 | 106 | 25 | 31 | 84 | 325 |
| **flow** | 1686 | 850 | 185 | 83 | 37 | 25 | 62 | 132 |
| **mip** | 1682 | 866 | 178 | 78 | 36 | 26 | 62 | 132 |
| **hungarian** | 1688 | 847 | 185 | 82 | 37 | 28 | 61 | 132 |
| **da** | 1607 | 689 | 235 | 108 | 33 | 19 | 81 | 288 |
| **equite** | 1655 | 897 | 168 | 83 | 43 | 24 | 58 | 132 |
| **mip_full** | 1618 | 740 | 286 | 92 | 49 | 16 | 57 | 202 |

## Fichiers produits (dossier `out/`)

**Faisabilité** (une seule fois par instance) :
- `feas_par_eleve.csv` — pour chaque paire (élève, bloc) : nb accessibles, nb vœux atteignables.
- `feas_par_occurrence.csv` — demande théorique vs capacité, cours tendus en tête.
- `feas_impossibles.csv` — paires structurellement bloquées.

**Par algo** :
- `assignment_<algo>.csv` — affectations (§11.1).
- `remplissage_<algo>.csv` — occupation par occurrence, alertes sous/dépassement.
- `equite_<algo>.csv` — rang moyen par (régime, langue).
- `non_affectes_<algo>.csv` — liste **nominative** avec cause.
- `satisfaction_<algo>.csv` — rangs par bloc, somme, pire bloc.
