# Mémoire du projet — à charger au début d'une nouvelle session

## Objectif

Écrire un système d'affectation des élèves de 2A aux occurrences de cours
électifs de Télécom Paris, avec plusieurs algorithmes comparables,
exécutable une fois par an. Cf. [`cahier_des_charges.md`](cahier_des_charges.md).

## État courant

- Voir le [`journal.md`](journal.md) pour la chronologie.
- Voir [`notes.md`](notes.md) pour les questions ouvertes.
- Voir [`resultats.md`](resultats.md) pour le dernier bench.
- Voir [`limites_structurelles.md`](limites_structurelles.md) pour le
  rapport encadrement.

## Décisions clés

- **Deux formats de données** : `data/` (simplifié, avec vœux réels) et
  `data/2026/` (Synapse réel, sans vœux). Adaptateur commun dans
  `src/preprocess.py`.
- **Vœux** : classement global d'UEs par élève, projeté sur chaque bloc.
  Un fichier `eleves_par_bloc.csv` peut fournir un classement par bloc,
  détecté automatiquement.
- **Priorité anglophone** : `BONUS_ANGLOPHONE` soustrait au coût quand un
  anglophone reçoit un cours en anglais.
- **Complétude par régime** :
  - **FISE** (étudiant) — 1 occurrence par bloc obligatoire (10 blocs :
    5 S1 + 5 S2, Module d'ouverture scindé S1/S2 dans `mip_full`).
  - **FISEA** (apprenti) — ≤ 3 ECUE par semestre (règle scolarité).
  - **Auditeur** — traité comme FISE flexible.
- **`mip_full` est l'algo recommandé pour la production** : seul à
  respecter toutes les contraintes (exclusion inter-blocs, unicité ECUE,
  complétude par régime, capacité, langue). 7 s sur 340 élèves.

## Structure

- `src/constantes.py` — source unique de vérité (mappings, créneaux).
- `src/model.py` — dataclasses `Student`, `Occurrence`, `Instance`.
- `src/preprocess.py` — chargement (2 formats supportés).
- `src/filters.py` — accessibilité (créneau, langue, FISEA, jours entreprise).
- `src/common.py` — helpers `rang(s, o)`, `cout(s, o)`.
- `src/algo_{rsd,flow,mip,hungarian,da,equite,mip_full}.py` — 7 algos.
- `src/feasibility.py` — analyse préalable.
- `src/verif_contraintes.py` — vérification post-affectation exhaustive.
- `src/verif_charge.py` — contrôle des crédits.
- `src/report.py` — métriques + rapport.
- `src/bench.py` — orchestrateur.
- `tools/{analyse_structurelle, bench_multi, make_ranking_par_bloc}.py`.
- `experiments/{algo_aceei, algo_upgrade, algo_waterfilling}.py` —
  approches non retenues, gardées pour comparaison.
- `app/streamlit_app.py` — interface interactive.

## Conventions

- Français pour le texte, anglais pour les identifiants techniques standards.
- Créneaux internes : `Lu-am | Lu-pm | Ma-am | Ma-pm | Me-am | Me-pm | Ve-am | Ve-pm`.
- Périodes internes : entiers `1..4`.
- Langue interne : `FR | EN`.
- Régime interne : `etudiant | apprenti | auditeur`.
- **Rangs 1-indexés partout** (1 = premier choix).
- Fichiers `src/*.py` < 200 lignes.

## Environnement

- Python 3.11+, dépendances dans `requirements.txt`.
- Libs custom (via `pip install --user` sous Windows) : `ortools`,
  `matching`, `fairpyx`, `idna`.
- Accès GPU `ssh gpu.enst.fr` disponible (pas nécessaire ici).

## Commandes utiles

```bash
python -m src.bench --data data                     # bench complet
python -m src.bench --data data --algo mip_full     # un seul algo
python -m tools.bench_multi data --seeds 10         # multi-seed
python -m tools.analyse_structurelle data/2026      # rapport structurel
python -m src.verif_contraintes data                # audit contraintes
python -m src.verif_charge data                     # audit crédits
python -m tools.make_ranking_par_bloc data          # génère eleves_par_bloc.csv
streamlit run app/streamlit_app.py                  # app
```

## Actions à faire quand les vœux Synapse 2026 seront disponibles

- Fournir `data/2026/voeux_par_bloc.csv` (mêmes colonnes que
  `data/eleves_par_bloc.csv`). Le préprocesseur le charge auto.
- Vérifier avec `feasibility.occurrences_sans_creneau(inst)` où placer
  les 7 Humanités sans créneau prédéfini.
- Récupérer avec la scolarité le mapping filière apprentie → 3 blocs
  obligatoires par semestre (CYBER, DSAI, RIO, SE — les 4 filières
  apprenties confirmées).

## Bug résolus notables

- **algo_equite ancien** : la boucle de swaps opérait sur une liste
  stale et créait des dépassements massifs de capacité (jusqu'à 192
  élèves dans un cours à 60 places). Corrigé en re-lisant `a[e][bloc]`
  à chaque itération. Impact : 1er choix passé de 67% à 56.5%.
