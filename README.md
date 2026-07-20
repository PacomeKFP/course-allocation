# Course Allocation — Télécom Paris 2ᵉ année

Système d'affectation des élèves de 2A aux occurrences de cours électifs
(tronc commun). Prend en entrée les listes d'élèves, de cours et de vœux
sortis de Synapse, produit en sortie un fichier d'affectation prêt à
réinjecter, plus un rapport d'analyse humainement lisible.

## Description

Chaque année, ~350 élèves doivent recevoir une occurrence pour chacun
des blocs obligatoires du tronc commun (Statistique, Optim, IA,
Sécurité, Droit, Économie du numérique, SEHS, Humanités, Modules
d'ouverture). Le problème est difficile car les contraintes
s'accumulent : créneaux de filière, jours d'entreprise pour les
apprentis, langue, capacités des salles, cohérence de l'emploi du temps.

Le projet fournit **7 algorithmes** d'affectation, un **vérificateur
exhaustif** des contraintes, une **analyse structurelle** des blocages,
un **bench multi-seed**, un **rapport comparatif** et une **app
Streamlit** pour l'exploration et l'édition manuelle.

Voir [`docs/cahier_des_charges.md`](docs/cahier_des_charges.md) pour la
spec métier complète et [`docs/algorithmes.md`](docs/algorithmes.md)
pour la pédagogie des approches.

## Installation

```bash
# Python 3.11+ recommandé
pip install -r requirements.txt
```

Aucune configuration spécifique n'est nécessaire — l'app Streamlit,
le CLI et les scripts fonctionnent immédiatement sur les données
fournies dans `data/`.

## Structure du projet

```
data/                    fichiers d'entrée
├── eleves.csv          format simplifié (avec vœux, cas de test)
├── cours.csv
├── filiere.csv
└── 2026/               format Synapse réel (sans vœux)

src/                     code de production
├── constantes.py       mappings filière→groupe, créneaux universels
├── model.py            dataclasses Instance, Student, Occurrence
├── preprocess.py       chargement des CSV (2 formats supportés)
├── filters.py          accessibilité (créneau, langue, FISEA, ...)
├── common.py           helpers coût + rang
├── algo_rsd.py         Random Serial Dictator (baseline)
├── algo_flow.py        Min-cost flow par bloc
├── algo_mip.py         MIP simple (CP-SAT)
├── algo_hungarian.py   Bipartite hongrois
├── algo_da.py          Deferred Acceptance (Gale-Shapley)
├── algo_equite.py      Local search au-dessus de flow
├── algo_mip_full.py    MIP intégral (toutes contraintes ; RECOMMANDÉ)
├── feasibility.py      analyse préalable structurelle
├── verif_contraintes.py  vérification exhaustive post-affectation
├── verif_charge.py     contrôle des crédits par élève
├── report.py           métriques + distributions
└── bench.py            orchestrateur qui lance tous les algos

experiments/             algos expérimentaux (non-prod)
├── algo_aceei.py       fairpyx (iterated matching équitable)
├── algo_upgrade.py     init aléatoire + swaps
├── algo_waterfilling.py  pire rang → promotions itératives
└── bench_aceei.py

tools/                   utilitaires ligne de commande
├── analyse_structurelle.py  génère les tableaux du rapport encadrement
├── bench_multi.py           multi-seed pour algos stochastiques
└── make_ranking_par_bloc.py  dérive vœux par bloc depuis vœux globaux

app/
└── streamlit_app.py    interface interactive (upload, run, édition)

docs/                    documentation
├── cahier_des_charges.md      spec métier de référence
├── algorithmes.md             pédagogie + références académiques
├── limites_structurelles.md   rapport pour l'encadrement
├── approches.md               résumé par algo
├── resultats.md               tableau de bench (regénéré)
├── journal.md                 chronologie du développement
├── memoire.md                 état à charger en session
└── notes.md                   questions ouvertes numérotées

.streamlit/              config app (thème clair)
```

## Utilisation

### CLI — bench complet

```bash
# Lance tous les algos, produit out/*.csv et docs/resultats.md
python -m src.bench --data data/

# Un seul algo
python -m src.bench --data data/ --algo mip_full

# Multi-seed pour les algos stochastiques (mean±std sur K seeds)
python -m tools.bench_multi data/ --seeds 10
```

### CLI — analyses standalone

```bash
# Analyse structurelle (profils × blocs, impossibles théoriques)
python -m tools.analyse_structurelle data/2026

# Faisabilité pré-algo (cours tendus, paires bloquées)
python -c "from src.preprocess import load; from src.feasibility import resume; \
           print(resume(load('data')))"

# Vérification exhaustive d'une affectation
python -m src.verif_contraintes data

# Contrôle de la charge (crédits)
python -m src.verif_charge data
```

### App interactive

```bash
streamlit run app/streamlit_app.py
```

Onglets : Récap · Faisabilité · Distribution des rangs · Non-affectés ·
Remplissage · Satisfaction par élève · Équité par groupe · Édition
manuelle avec download.

## Algorithmes disponibles

| Algo | Type | Toutes contraintes | Recommandation |
|---|---|:---:|---|
| `rsd` | Baseline aléatoire | Non | Référence |
| `flow` | Min-cost flow (networkx) | Non (violent exclusion inter-blocs) | Rapide |
| `mip` | CP-SAT simple | Non | Comparaison |
| `hungarian` | Bipartite (scipy) | Non | Comparaison |
| `da` | Deferred Acceptance | Non | Stability |
| `equite` | Flow + local search | Non | Meilleur rang moyen |
| **`mip_full`** | **CP-SAT intégral** | **Oui** | **Production** |

**`mip_full`** est le seul algo qui garantit le respect simultané de :
accessibilité, exclusion inter-occurrences (même créneau/période),
unicité ECUE, complétude par régime (FISE = 1 par bloc, FISEA ≤ 3 par
semestre), capacité et bonus anglophone.

Voir [`docs/algorithmes.md`](docs/algorithmes.md) pour les détails
académiques et références.

## Formats de données

Deux formats de données sont supportés par `src/preprocess.load()` :

1. **Format simplifié** (`data/eleves.csv`, `cours.csv`, `filiere.csv`)
   — jeu de test avec vœux réels ; filière codée en lettre A/B/C ;
   classement global d'UEs par élève.

2. **Format Synapse 2026** (`data/2026/*.csv`) — extraction Alexia ;
   filière nommée (`DSAI`, `MACS`, …) ; blocs et FISEA explicites ;
   les vœux doivent être fournis séparément dans `voeux_par_bloc.csv`.

Voir §4 de [`docs/cahier_des_charges.md`](docs/cahier_des_charges.md).

## Documentation

- [Cahier des charges](docs/cahier_des_charges.md) — spec métier
- [Panorama pédagogique des algorithmes](docs/algorithmes.md) —
  principe, motivation, forces, faiblesses, ~30 références
- [Limites structurelles](docs/limites_structurelles.md) — rapport
  pour l'encadrement (impossibles apprentis, capacités tendues)
- [Résultats de bench](docs/resultats.md) — comparaison numérique
- [Journal](docs/journal.md), [Mémoire](docs/memoire.md),
  [Notes](docs/notes.md) — chronologie et questions ouvertes

## Contribution

- Le code est en français, les identifiants techniques en anglais.
- Chaque fichier `src/*.py` fait moins de 200 lignes.
- Tests par vérification empirique : lancer `python -m src.bench` et
  vérifier que les métriques ne régressent pas.
- Convention créneau : `Lu-am | Lu-pm | Ma-am | Ma-pm | Me-am | Me-pm
  | Ve-am | Ve-pm` (le jeudi n'accueille pas de cours).
- Convention rang : **1-indexé** partout (1 = premier choix).

## Licence

Usage interne Télécom Paris. Contact : Pacome K.
