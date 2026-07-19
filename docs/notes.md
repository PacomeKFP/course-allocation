# Notes, remarques et questions ouvertes

Chaque point est numéroté pour être référençable. Les statuts :
- 🟠 **ouvert** — décision non tranchée, à lever avec la scolarité (Alexia).
- 🟢 **résolu** — décision prise (voir `journal.md` pour la date).
- 🔴 **problème donnée** — incohérence à faire corriger côté source.

---

## Sur les données

### N1 · Deux formats coexistent 🟢

`data/` (simplifié, avec vœux réels) et `data/2026/` (Synapse réel, sans vœux).
Décision : préprocesseur unifié qui gère les deux formats. Cf. `src/preprocess.py`.

### N2 · Le format simplifié n'a pas de `FISEA` explicite 🟡

On l'infère par mot-clé dans le titre (« apprentis », « FISEA ») pour rester
compatible ; c'est une approximation. Le vrai marqueur est présent dans le
format 2026.

### N3 · Codes UE différents entre les deux fichiers de cours 🔴

Exemple : `CSC_OEL07_TP` (simplifié) vs `CSC_4EL07_TP` (2026-2027). Idem
`ECO_OEL30_TP` vs `ECO_4TC40_TP`. Il faudra un mapping si on doit croiser.
Pour l'instant, chaque instance est autonome et n'utilise qu'un seul jeu.

### N4 · Bloc « SEHS » dans le format simplifié, plusieurs blocs dans le format réel 🔴

Le format simplifié fusionne « SEHS », « Économie du numérique », etc.
Le format 2026 distingue « Bloc Eco Num », « Bloc module d'ouverture SEHS »,
« Humanités Contemporaines », etc. Cela affecte le nombre de blocs
obligatoires. À trancher pour la version production.

### N5 · Créneaux vides pour certaines Humanités 🟢

Format 2026 : plusieurs occurrences d'Humanités ont un `Créneau prédéfini` vide
(« S2P3 ou S2P4 »). Décision : on **exclut** ces occurrences des affectations
tant que leur horaire n'est pas fixé (le filtre `raison_rejet` renvoie
« créneau non fixé »). **En complément**, `feasibility.occurrences_sans_creneau`
propose des créneaux candidats classés par nombre de demandeurs libres.

### N6 · Filières A/B/C simplifiées 🟢

Mapping centralisé dans `src/constantes.py` (`FILIERE_TO_GROUPE`). Le
préprocesseur applique la traduction pour les deux formats. Codes filière
sans mapping (TSIA, SD, ENTP, RECH) → aucune contrainte horaire imposée.

### N7 · Jours bloqués des apprentis 🟢

Résolu par déduction : un apprenti a UNE filière → 2 créneaux de cours →
1-2 jours à l'école parmi {Lu, Ma, Me, Ve}. Les 2 autres jours (parmi ces 4)
sont d'entreprise. Le jeudi est chômé. `jours_entreprise_apprenti(groupe, periode)`
dans `src/constantes.py` fait le calcul. Cette contrainte fait tomber le taux
d'affectation observé de 98.3% à 95.7% — 60 paires (élève, bloc) deviennent
structurellement impossibles et sont exposées dans `feas_impossibles.csv`.

### N8 · Vœux : un seul classement global 🟢

Retenu comme représentation « simple ». On génère aussi une version par bloc
via `tools/make_ranking_par_bloc.py` (dérivée triviale du classement global :
on filtre les UEs de chaque bloc dans l'ordre global). L'adaptateur unifie.

### N9 · Places déjà occupées 🟡

Format simplifié : pas de champ. Format 2026 : `Nbinscrits = 0` partout dans
l'extrait. On lit la colonne mais elle vaut 0 aujourd'hui.

---

## Sur les règles métier

### N10 · Blocs obligatoires 🟢

Hypothèse : tous les blocs présents dans le fichier de cours sont obligatoires
pour tout le monde. À raffiner si Alexia confirme des exceptions (par ex. les
auditeurs sans HSS).

### N11 · Priorité anglophone 🟢

Bonus dans la fonction de coût (paramètre `BONUS_ANGLOPHONE` dans `src/model.py`,
valeur par défaut `-2` sur le rang effectif). S'applique quand un élève marqué
anglophone reçoit une occurrence en anglais.

### N12 · Charge par période 🟡

Le cahier dit « de l'ordre de 2 à 3 par période ». Non contrôlé par les algos
en version 1 (on laisse la structure des blocs répartir naturellement). À
implémenter comme contrainte souple si des dérives apparaissent au bench.

### N13 · Unicité UE (§8.7) 🟡

Un élève reçoit au plus une occurrence par UE. Vrai « par construction » vu
qu'un même UE n'apparaît que dans un seul bloc. À vérifier sur le format 2026.

---

## Incertitudes algorithmiques

### N14 · Hungarian et capacités > 1 🟢

L'algo hongrois est un-à-un. Pour supporter des capacités, on duplique chaque
occurrence `c` fois (`c = capacité`). Implémentation dans `src/algo_hungarian.py`.

### N15 · Deferred Acceptance et blocs multiples 🟡

La lib `matching` (variante hospitals/residents) est prévue pour un problème
d'appariement unique. Pour couvrir plusieurs blocs, on **applique DA bloc par
bloc**, ce qui perd la vision globale (charge par période). Note à porter dans
le rapport de bench.

### N16 · A-CEEI (fairpyx) et notre modèle 🟢

`fairpyx` n'a pas d'A-CEEI direct : on utilise
`iterated_maximum_matching_adjusted` comme proxy équitable. Isolé dans
`experiments/` pour ne pas polluer le bench principal. Résultats
respectables (64% de premier choix vs 58% pour flow) mais moins d'affectations
totales (87.4% vs 95.7%). À réserver pour comparaison.
