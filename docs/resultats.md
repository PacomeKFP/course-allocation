# Résultats comparatifs des algorithmes

Instance : **340 élèves**, **67 occurrences**, **9 blocs**, soit 3060 paires (élève, bloc).

## Tableau récapitulatif

| Algo | Temps (s) | Taux affect. | Rang moyen | 1er choix | Top-3 |
|---|---:|---:|---:|---:|---:|
| **rsd** | 0.0 | 92.0% | 0.83 | 59.4% | 91.6% |
| **flow** | 0.8 | 98.3% | 0.70 | 58.0% | 93.6% |
| **mip** | 2.4 | 98.3% | 0.70 | 58.4% | 93.7% |
| **hungarian** | 1.5 | 98.3% | 0.70 | 58.3% | 93.6% |
| **da** | 0.9 | 92.5% | 0.80 | 59.6% | 92.0% |
| **aceei** | 2.9 | 91.3% | 0.80 | 63.0% | 91.3% |

*Rang 1-indexé : `1` = premier choix, `2` = deuxième, etc. Rang moyen ici en 0-indexé (0 = 1er choix).*

## Distribution des rangs obtenus

Nombre d'affectations à chaque rang (top 6). « ≥7 » regroupe les rangs éloignés.

| Algo | 1 | 2 | 3 | 4 | 5 | 6 | ≥7 | non affecté |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **rsd** | 1674 | 692 | 214 | 95 | 26 | 27 | 88 | 244 |
| **flow** | 1746 | 903 | 167 | 81 | 37 | 21 | 53 | 52 |
| **mip** | 1758 | 884 | 177 | 77 | 39 | 20 | 53 | 52 |
| **hungarian** | 1753 | 881 | 180 | 83 | 38 | 21 | 52 | 52 |
| **da** | 1688 | 695 | 220 | 101 | 29 | 18 | 79 | 230 |
| **aceei** | 1760 | 574 | 217 | 87 | 37 | 25 | 93 | 267 |

## Notes de lecture

- **flow / mip / hungarian** convergent vers le même optimum : ils minimisent la somme des rangs sous les contraintes de capacité, avec un fallback « non-affecté » à coût prohibitif. En pratique, ils affectent le maximum de paires possible tout en donnant à ~58 % des élèves leur premier choix.
- **rsd** (Random Serial Dictator) est le baseline : 30 lignes de code, très rapide, mais plus d'échecs (~8 %) car les derniers servis n'ont plus de place. Utile comme référence.
- **da** (Deferred Acceptance) offre la robustesse à la déclaration (l'élève n'a pas intérêt à mentir) et gère naturellement la priorité anglophone via l'ordre des préférences côté occurrence. Sur la métrique de rang moyen il est comparable à RSD.
- **aceei** (ici : `iterated_maximum_matching_adjusted` de fairpyx) cible l'équité : il donne plus souvent le **premier** choix (63 %) au prix d'un taux d'affectation plus faible. Voir `docs/notes.md` N16 sur l'absence d'A-CEEI natif dans fairpyx.

## Fichiers produits

Pour chaque algo, dans `out/` :

- `assignment_<algo>.csv` : affectations `eleveID;bloc;id_occ` (format §11.1).
- `remplissage_<algo>.csv` : occupation par occurrence.
- `equite_<algo>.csv` : rang moyen par (régime, langue).
