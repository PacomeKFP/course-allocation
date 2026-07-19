# Résultats comparatifs des algorithmes

Instance : **340 élèves**, **67 occurrences**, **9 blocs**, soit 3060 paires (élève, bloc).

## Tableau récapitulatif

| Algo | Temps (s) | Taux affect. | Rang moyen | 1er choix | Top-3 |
|---|---:|---:|---:|---:|---:|
| **flow** | 0.9 | 95.7% | 0.75 | 57.6% | 92.9% |

*Rang 1-indexé : `1` = premier choix, `2` = deuxième, etc. Rang moyen ici en 0-indexé (0 = 1er choix).*

## Distribution des rangs obtenus

Nombre d'affectations à chaque rang (top 6). « ≥7 » regroupe les rangs éloignés.

| Algo | 1 | 2 | 3 | 4 | 5 | 6 | ≥7 | non affecté |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **flow** | 1686 | 850 | 185 | 83 | 37 | 25 | 62 | 132 |

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
