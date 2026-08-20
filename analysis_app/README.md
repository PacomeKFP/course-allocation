Mini-app d'analyse des vœux non assignés

Lancer :

```
pip install -r requirements.txt
streamlit run analysis_app/app.py
```

L'application charge les mêmes fichiers que le pipeline et permet de :
- lister les vœux pour lesquels aucune occurrence n'est accessible selon `Feasibility` ;
- afficher, par étudiant, les occurrences choisies, les raisons détaillées et une reconstitution simple de son emploi du temps (créneaux occupés par la filière, jours d'entreprise pour les apprentis).
