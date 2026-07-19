# Journal de travail

Trace chronologique des étapes importantes du développement. Voir aussi :
- [`memoire.md`](memoire.md) — état à charger au début d'une future session
- [`notes.md`](notes.md) — questions, remarques, incompréhensions, décisions ouvertes
- [`cahier_des_charges.md`](cahier_des_charges.md) — spécification métier

---

## 2026-07-19 — J1 · Cadrage et démarrage

**Compris**

- Deux jeux de données coexistent :
  - `data/2026/` — format Synapse réel (§4 du cahier) : `Idoccur`, `Bloc`, `FISEA`, filières nommées (`DSAI`, `MACS`, …).
  - `data/{eleves,cours,filiere}.csv` — format simplifié « année dernière » : filière codée `A/B/C`, `info ∈ {apprenti, international, ""}`, **un unique classement global** de toutes les UEs par élève.
- Répartition du fichier simplifié : 260 étudiants classiques, 30 apprentis, 50 internationaux (anglophones).

**Décisions de cadrage**

1. Cible principale = format simplifié pour le bench (car on y a les vœux réels). Un adaptateur lit aussi le format 2026-2027.
2. Vœux : partir du classement global existant, **puis** produire une seconde version avec un classement par bloc (via `tools/make_ranking_par_bloc.py`), et un adaptateur qui unifie les deux.
3. Approches à implémenter (toutes, cf. §13 du cahier) : RSD (baseline), min-cost flow, MIP CP-SAT, Hungarian, Deferred Acceptance, A-CEEI. Puis bench comparatif.
4. Priorité anglophone : bonus dans la fonction de coût.
5. Blocs obligatoires : **tous** les blocs présents dans le fichier de cours, pour tout le monde (à raffiner plus tard si Alexia confirme des exceptions par régime).
6. Streamlit : à la toute fin, séparé de `src/`.

**Structure du projet**

```
course-allocation/
├── data/                  # fichiers d'entrée
├── docs/                  # doc + notes
├── src/                   # code métier (préprocessing + algos + reporting)
├── tools/                 # petits utilitaires (génération de fichiers dérivés)
├── app/                   # app Streamlit (fin de projet)
├── .gitignore
└── README.md
```

**Environnement**

- `conda env base` (Python 3.11).
- Libs déjà présentes : pandas, numpy, scipy, networkx, streamlit.
- Libs installées ce jour (`pip install --user`) : `ortools`, `matching`, `fairpyx`, `idna`
  (le dernier était manquant et cassait Streamlit au démarrage).

---

## 2026-07-19 — J1 · Fin de la journée : tout est fonctionnel

**Livrables**

- `src/preprocess.py` — adaptateur pour les deux formats de données.
- `src/filters.py` — accessibilité (élève, occurrence) avec raison de rejet.
- `src/common.py` — coût partagé + helpers.
- `src/algo_{rsd,flow,mip,hungarian,da,aceei}.py` — 6 approches, chacune ≤ 80 lignes.
- `src/report.py` — métriques + causes de non-affectation.
- `src/bench.py` — orchestrateur qui lance tous les algos et écrit `docs/resultats.md`.
- `tools/make_ranking_par_bloc.py` — génère `data/eleves_par_bloc.csv`.
- `app/streamlit_app.py` — UI minimale (upload, run, tabs, éditable).
- `docs/approches.md` — documentation par approche.
- `docs/resultats.md` — rapport de bench comparatif (regénéré à chaque run).

**Résultats de bench (données simplifiées, 340 élèves × 9 blocs = 3060 paires)**

| Algo | Temps (s) | Taux affect. | Rang moyen | 1er choix |
|---|---:|---:|---:|---:|
| rsd | 0.0 | 92.0% | 0.83 | 59.4% |
| flow | 0.8 | 98.3% | 0.70 | 58.0% |
| mip | 2.4 | 98.3% | 0.70 | 58.4% |
| hungarian | 1.5 | 98.3% | 0.70 | 58.3% |
| da | 0.9 | 92.5% | 0.80 | 59.6% |
| aceei | 2.9 | 91.3% | 0.80 | 63.0% |

flow / mip / hungarian atteignent l'optimum (aux tie-breaks près). aceei
maximise la part de premier choix au prix d'un taux d'affectation plus faible.
Détails et commentaires dans [`resultats.md`](resultats.md).

**Prochaines étapes possibles**

1. Faire tourner le bench sur le format Synapse 2026 quand les vœux seront
   disponibles (cf. `notes.md` N3, N4).
2. Ajouter la contrainte de charge par période (`notes.md` N12) au MIP —
   c'est le seul algo où c'est facilement modélisable.
3. Écrire un vrai A-CEEI si fairpyx en fournit un un jour (`notes.md` N16).
