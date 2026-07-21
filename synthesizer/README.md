# Synthesizer — génération de jeux de données de test

Application Streamlit dédiée à la génération de campagnes fictives pour
tester le solveur d'affectation sans données réelles.

## Utilisation

```bash
streamlit run synthesizer/app.py
```

Configure la promotion (taille, part apprentis/anglophones), génère et
télécharge trois CSV compatibles avec le pipeline principal :

- `etudiants_anonymises.csv` (format Synapse)
- `structure-export.csv` (vœux fictifs)
- Optionnellement une nouvelle Liste ECUE

**Non versionné** (dossier dans `.gitignore`), à déployer séparément.
