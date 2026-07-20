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
| **mip_full** | 8.5 | 93.4% | 1.80 | 1 | 2 | 3 | 12 | 56.2% | 92.5% | 4.2% |

*Rangs 1-indexés partout : `1` = premier choix. « Méd » = médiane, « Q75 » = troisième quartile, « D9 » = neuvième décile, « ≥5 » = part d'affectations avec rang ≥ 5 (élèves mal servis).*

## Distribution des rangs obtenus

| Algo | 1 | 2 | 3 | 4 | 5 | 6 | ≥7 | non affecté |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **mip_full** | 1606 | 764 | 275 | 94 | 45 | 18 | 56 | 202 |

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
