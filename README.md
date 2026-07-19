# Course allocation — Télécom Paris 2A

Affectation des élèves de 2ᵉ année aux occurrences de cours électifs.
Cf. [`docs/cahier_des_charges.md`](docs/cahier_des_charges.md) pour la spec métier.

## Structure

```
data/                   fichiers d'entrée (CSV)
docs/                   spec + journal + mémoire + notes
src/                    code métier (préprocessing + algos + reporting)
tools/                  petits utilitaires (fichiers dérivés)
app/                    app Streamlit (fin de projet)
```

## Utilisation rapide

```bash
# 1. Charger une instance et lancer un algo
python -m src.bench --data data/ --algo flow

# 2. Lancer tous les algos et produire le rapport comparatif
python -m src.bench --data data/ --all
```

Voir [`docs/memoire.md`](docs/memoire.md) pour l'état du projet.
