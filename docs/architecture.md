# Architecture

Vue d'ensemble du pipeline et de la hiérarchie de classes.

## Pipeline de haut niveau

```
[etudiants.csv]  [campagne.csv]  [ecue.csv (optionnel)]
        │              │                 │
        └──────────────┴─────────────────┘
                       │
                       ▼
              data.build_campaign
                       │
                       ▼
                   Campaign
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
     ▼                 ▼                 ▼
Feasibility     PriorityChain        Report
(par-paire)     (étape 1)         (post-affect.)
     │                 │                 ▲
     │                 ▼                 │
     │           partial_assign          │
     │                 │                 │
     └────────►  MipSolver  ─────────────┘
                       │
                       ▼
                  Assignment
                       │
                       ▼
       exporter.export_synapse_import
                       │
                       ▼
              out/synapse_import.csv
              out/not_assigned.csv
              out/filling.csv
              out/stats_*.csv
```

## Modules et responsabilités

### `src/data/` — chargement et modèle

- `constants.py` : mappings et bornes stables (FILIERE_TO_GROUPE,
  SLOTS_BY_GROUP, BIG_M, COST_POWER, ENGLISH_MATCH_BONUS).
- `model.py` : dataclasses immuables `Student`, `Occurrence`, `Voeu`,
  `Campaign` + alias `Assignment = dict[(id_student, id_demande) → id_occ|None]`.
- `loaders.py` : trois lecteurs `load_students`, `load_ecue`,
  `load_campaign` + assembleur `build_campaign`.
- `default_ecue.csv` : liste ECUE embarquée (fallback).

### `src/rules/` — faisabilité et contraintes

- `Feasibility` : 5 méthodes par-paire renvoyant `None` ou une raison
  textuelle. `check(s, o)` accumule les raisons ; utilisé aussi pour
  l'explicabilité dans les rapports.
- `OccurrenceConstraints` : émet les groupes d'occurrences
  mutuellement exclusives (même instant, même UE).
- `StudentConstraints` : dérive la table des paires (élève, occ)
  interdites, alimentée par `Feasibility`.

### `src/solvers/` — algorithmes

- `Solver` (ABC) : contrat `solve(campaign, pre_assignment=None) → Assignment`.
- `PriorityChain` : applique séquentiellement des priorités
  (anglophones→EN, apprentis→FISEA). Une méthode = une priorité.
- `MipSolver` : CP-SAT OR-Tools, 7 méthodes courtes
  (`_variables`, `_one_per_demande`, `_capacity`, `_exclusions`,
  `_objective`, `_extract`, `solve`). Coût = `rang^cost_power` moins
  bonus anglophone. Slack pénalisé à BIG_M pour les demandes non-servies.

### `src/reporting/` — post-traitement

- `exporter.export_synapse_import` : CSV au format `structure-import`.
- `Report` : 5 vues (`not_assigned`, `filling`, `stats_global`,
  `stats_per_demande`, `stats_compensation`).

### `src/pipeline.py` — orchestration + CLI

Compose les briques : `build_campaign → PriorityChain → Solver → Report`.

### `src/utils/` — helpers transverses

Uniquement `group_by(items, key)`.

### `app/streamlit_app.py` — interface

Upload → run → 6 onglets → download.

## Extension

Ajouter une nouvelle priorité :
```python
class PriorityChain:
    def __init__(self, ...):
        self.rules = [..., self.ma_nouvelle_priorite]

    def ma_nouvelle_priorite(self, campaign, assignment, remaining):
        ...
```

Ajouter un nouveau solveur :
```python
class MonSolveur(Solver):
    NAME = "custom"
    def solve(self, campaign, pre_assignment=None) -> Assignment:
        ...
```

Ajouter une contrainte inter-occurrences :
```python
class OccurrenceConstraints:
    def ma_regle(self, occurrences) -> list[list[str]]:
        ...
    def build(self, occurrences):
        return dedup([self.same_instant(...), self.same_ue(...), self.ma_regle(...)])
```

Ajouter une nouvelle règle de faisabilité :
```python
class Feasibility:
    def ma_regle(self, s, o) -> str | None: ...
    def check(self, s, o):
        return [msg for msg in (..., self.ma_regle(s, o)) if msg]
```
