# Course Allocation — Télécom Paris 2A

Affectation automatique des élèves de 2ᵉ année aux occurrences de cours
électifs, à partir des fichiers d'export/import Synapse.

## Ce que fait le programme

1. Lit une **liste d'étudiants** + un **export de campagne de vœux** (formats
   Synapse authentiques). La liste ECUE est optionnelle (défaut embarqué).
2. Applique des **priorités métier** avant tout calcul (anglophones sur les
   cours en anglais, apprentis sur les FISEA).
3. Résout le reste par un **MIP CP-SAT** qui respecte simultanément :
   accessibilité (créneau/langue/FISEA/jour d'entreprise), exclusion
   inter-occurrences au même instant, unicité des ECUE dans l'année,
   capacité, une affectation par (élève, demande).
4. Produit un **CSV au format `structure-import` Synapse** + un rapport
   multi-vues (non-affectés avec cause, remplissage, distribution des
   rangs par demande, compensation par élève).

## Installation

```bash
pip install -r requirements.txt
```

Python 3.11+.

## Utilisation

### CLI

```bash
python -m src.pipeline data/samples/etudiants_anonymises.csv  data/samples/campagne_synthetique.csv  --out out/ --time-limit 60
```

### App interactive

```bash
streamlit run app/streamlit_app.py
```

Charger deux CSV dans la sidebar (étudiants + campagne), régler la
puissance du coût (rang^p, défaut 2), lancer, explorer les onglets,
télécharger le CSV d'import Synapse.

### API Python

```python
from src.pipeline import run_campaign
campaign, assignment, report = run_campaign(
    "data/samples/etudiants_anonymises.csv",
    "data/samples/campagne_synthetique.csv",
    out_dir="out/",
)
print(report.stats_global())
```

## Structure

```
src/
├── data/           chargement, modèle, constantes (Student, Occurrence,
│                   Voeu, Campaign, Assignment)
├── rules/          Feasibility (par-paire), OccurrenceConstraints,
│                   StudentConstraints
├── solvers/        Solver (ABC), PriorityChain, MipSolver
├── reporting/      exporter Synapse, Report (5 vues)
├── utils/          helpers transverses
└── pipeline.py     run_campaign + CLI

app/streamlit_app.py       interface interactive
data/                      jeux de données
docs/                      documentation (algorithmes, limites, spec)
old/                       ancien code, gardé pour référence
files/                     échantillons fournis par la scolarité
```

Chaque fichier `src/*.py` fait **moins de 100 lignes**.
Identifiants en anglais, commentaires en français.

## Formats de données

### Entrée obligatoire 1 — étudiants
`etudiants_anonymises.csv` (Synapse) : colonnes `Id Personne`,
`IDDossierEtudiant`, `Régime Inscrip.` (Etudiant / Apprentis /
Auditeur libre), `Francophone` (OUI/NON), `Filieres` (séparés par `$$`).

### Entrée obligatoire 2 — vœux
`structure-export ...csv` (Synapse) : une ligne par (élève, demande),
colonnes `PersID`, `IDDemande`, `IDOccur Choix 1..14`. Une ligne sans
aucun choix = demande non concernée pour l'élève (elle est ignorée).

### Entrée optionnelle 3 — ECUE
`Liste ECUE ...csv` : colonnes `Idoccur`, `Idue`, `Codeue`,
`Intituleoccur`, `Periode`, `Bloc`, `Créneau prédéfini`, `Nbinscrits`,
`Effectifmin`, `Effectifmax`, `Langues`, `FISEA`. Sans ce fichier,
`src/data/default_ecue.csv` est utilisé.

### Sortie — pour Synapse
`out/synapse_import.csv` au format `structure-import` : une ligne par
étudiant, colonnes `IDDemande N` + `IDOccur N` pour chaque demande.

## Rapports supplémentaires produits

- `out/not_assigned.csv` — paires non affectées avec cause diagnostique
- `out/filling.csv` — occurrences avec effectifs / seuils / flags
- `out/stats_per_demande.csv` — rang moyen et pire par demande
- `out/stats_compensation.csv` — équité par élève (rangs cumulés)

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — schéma des classes
- [`docs/algorithmes.md`](docs/algorithmes.md) — principe pédagogique
- [`docs/limites_structurelles.md`](docs/limites_structurelles.md) —
  rapport à destination de l'encadrement (impossibilités structurelles)
- [`docs/cahier_des_charges.md`](docs/cahier_des_charges.md) — spec métier

## Convention de développement

- Identifiants (fichiers, fonctions, variables) : **anglais**
- Docstrings et commentaires : **français**
- Un fichier `src/*.py` : **≤ 100 lignes**
- Un fichier = une responsabilité claire
