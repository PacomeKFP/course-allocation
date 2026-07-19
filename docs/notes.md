# Notes, remarques et questions ouvertes

Chaque point est numéroté pour être référençable. Les statuts :
- 🟡 **ouvert** — décision non tranchée, à lever avec la scolarité (Alexia).
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

### N5 · Créneaux vides pour certaines Humanités 🟡

Format 2026 : plusieurs occurrences d'Humanités ont un `Créneau prédéfini` vide
(« S2P3 ou S2P4 »). Décision provisoire : on **exclut** ces occurrences des
affectations tant que leur horaire n'est pas fixé, en signalant l'exclusion.

### N6 · Filières A/B/C simplifiées 🟡

Le format simplifié utilise des lettres (`A|B|C`) directement, chaque étudiant
n'ayant qu'une seule lettre. Le format réel utilise des codes (`DSAI`, `MACS`, …)
et chaque étudiant en a deux. Comportement : dans le simplifié, on prend
`filiere` comme groupe direct ; dans le 2026, on résout d'abord chaque code
→ groupe A/B/C via `filiere.csv`, puis on prend l'union.

### N7 · Jours bloqués des apprentis non fournis 🟡

Le cahier dit « les jours qui ne concernent pas la filière de l'apprenti » mais
aucun fichier ne les explicite. Hypothèse par défaut : **aucun jour bloqué en
plus** de la filière (le jeudi n'a pas cours, il n'y a donc rien à retirer).
À raffiner si Alexia confirme un jour d'entreprise fixe (typiquement lundi).

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

### N16 · A-CEEI (fairpyx) et notre modèle 🟡

`fairpyx` attend des utilités par « panier de cours ». Passer des rangs à des
utilités additives + définir les paniers admissibles va demander une couche de
traduction. Attention : perf peut être limite pour 340 élèves × plusieurs
blocs. À évaluer.
