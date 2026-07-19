# Mémoire du projet — à charger au début d'une nouvelle session

## Objectif

Écrire un système d'affectation des élèves de 2A aux occurrences de cours électifs
de Télécom Paris, avec plusieurs algorithmes comparables, exécutable une fois par
an. Cf. [`cahier_des_charges.md`](cahier_des_charges.md).

## État courant

- Voir le [`journal.md`](journal.md) pour la chronologie.
- Voir [`notes.md`](notes.md) pour les questions ouvertes et incertitudes à lever
  avec la scolarité (Alexia).

## Décisions clés déjà prises

- **Deux formats de données** : `data/` (simplifié) et `data/2026/` (Synapse réel).
  Le préprocesseur produit un modèle interne unifié (`src/model.py`).
- **Vœux** : le classement global des UEs par élève est projeté sur chaque bloc.
  Une seconde version avec un classement par bloc existe (`tools/make_ranking_par_bloc.py`).
- **Priorité anglophone** : bonus dans la fonction de coût (paramétrable).
- **Tous les blocs sont obligatoires pour tout le monde** (hypothèse par défaut,
  à confirmer avec Alexia).
- **Algos implémentés** : RSD, min-cost flow, MIP CP-SAT, Hungarian, Deferred
  Acceptance, A-CEEI. Bench comparatif dans `src/bench.py`.

## Structure

- `src/model.py` — dataclasses `Student`, `Occurrence`, `Instance`, `Assignment`.
- `src/preprocess.py` — chargement d'une instance depuis un dossier de CSV.
- `src/filters.py` — accessibilité (élève, occurrence) après créneaux/langue/FISEA.
- `src/algo_*.py` — un fichier par approche, ≤ ~100 lignes chacun.
- `src/report.py` — métriques + causes de non-affectation.
- `src/bench.py` — lance tous les algos, produit `docs/resultats.md`.
- `tools/make_ranking_par_bloc.py` — dérive `eleves_par_bloc.csv`.
- `app/streamlit_app.py` — interface minimale.

## Conventions

- Français pour le texte, anglais pour les identifiants techniques standards.
- Créneaux internes : `Lu-am | Lu-pm | Ma-am | Ma-pm | Me-am | Me-pm | Ve-am | Ve-pm`.
- Périodes internes : entiers `1..4` (S1-P1 → 1, S1-P2 → 2, S2-P3 → 3, S2-P4 → 4).
- Langue interne : `FR | EN`.
- Régime interne : `etudiant | apprenti | auditeur`.

## Environnement

- `conda env base`, Python 3.11.
- Libs custom installées via `pip install --user` : `ortools`, `matching`, `fairpyx`, `idna`.
- Accès GPU disponible via `ssh gpu.enst.fr` (pas nécessaire vu la taille ≈ 350 élèves).

## Commandes utiles

```bash
# Bench complet (recrée out/ + docs/resultats.md)
python -m src.bench --data data

# Un seul algo
python -m src.bench --data data --algo flow

# Générer le classement par bloc dérivé
python -m tools.make_ranking_par_bloc data

# App
streamlit run app/streamlit_app.py
```

## État au 2026-07-19

- **Terminé** : préprocesseur, 6 algos, reporting, bench, docs, app Streamlit.
- **À faire quand les vœux Synapse 2026 seront disponibles** : brancher le
  format Synapse dans le bench (le préprocesseur est déjà prêt, il faut juste
  fournir un `voeux_par_bloc.csv` similaire à `eleves_par_bloc.csv`).
