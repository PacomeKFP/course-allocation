# Limites structurelles du système d'affectation

> **Public** : encadrement pédagogique, scolarité, direction. Aucun prérequis
> technique.
>
> **Objet** : identifier, indépendamment des vœux exprimés par les élèves,
> quels profils étudiants peuvent ou ne peuvent pas structurellement recevoir
> une affectation dans chaque bloc, et où la capacité totale offerte est
> insuffisante face à la taille de la promotion.

---

## 1. Pourquoi ce document

Notre algorithme d'affectation atteint aujourd'hui **95,7 %** de paires
(élève × bloc) satisfaites sur les données 2026-2027. Les 4,3 % qui manquent
**ne peuvent pas être récupérés en changeant d'algorithme** : ils viennent
de contraintes physiques de l'offre de cours. Ce document en fait
l'inventaire pour ouvrir une discussion avec la scolarité sur les
ajustements possibles côté offre.

Le raisonnement est **structurel** : nous ne regardons ni les vœux, ni les
choix concrets des élèves. Nous ne regardons que la combinaison
« profil × créneaux offerts par bloc ».

---

## 2. Le cadre horaire

La semaine de tronc commun est découpée en **8 demi-journées** :
Lu-am, Lu-pm, Ma-am, Ma-pm, Me-am, Me-pm, Ve-am, Ve-pm. Le jeudi n'accueille
pas de cours.

Chaque filière de spécialisation appartient à un **groupe de créneaux
(A, B ou C)**. Chaque groupe réserve **deux demi-journées par période** pour
ses propres cours ; ces créneaux sont donc indisponibles pour les cours du
tronc commun de l'élève.

| Groupe | Semestre 1 (P1, P2) | Semestre 2 (P3, P4) |
|:---:|:---:|:---:|
| **A** | Lu-am, Me-pm | Lu-pm, Ve-am |
| **B** | Lu-pm, Ve-am | Lu-am, Me-pm |
| **C** | Ma-am, Ve-pm | Ma-am, Ve-pm |

**Propriété structurante :** deux créneaux ne sont jamais réservés par
aucune filière — **Ma-pm** et **Me-am**. Ils sont donc libres pour tous les
élèves classiques et représentent les seuls emplacements naturels pour un
cours réellement commun à toute la promotion.

---

## 3. Les profils d'étudiant

Un profil se caractérise par trois axes indépendants :

- **Régime** : `Étudiant`, `Apprenti`, ou `Auditeur libre` (élève d'échange PEI) ;
- **Langue** : `Francophone (FR)` ou `Anglophone (EN)` ;
- **Filières** :
  - Un étudiant classique en a **2** (typiquement `A+B`, `A+C` ou `B+C`).
  - Un apprenti en a **1** (`A`, `B`, ou `C`) et, en plus, deux jours
    d'entreprise par semaine. Ces jours d'entreprise sont mécaniquement les
    deux jours ouvrés hors filière (le jeudi étant chômé pour tous).
  - Un auditeur en a **0**.

Contraintes de langue : un élève anglophone ne suit, **au premier semestre
uniquement**, que des cours en anglais. Au second semestre, la contrainte
disparaît pour tous.

---

## 4. Créneaux réellement libres par profil

Le tableau ci-dessous donne, pour chaque profil-type, le nombre de
demi-journées où l'élève est physiquement libre d'assister à un cours du
tronc commun. Une occurrence de cours placée en dehors de ces créneaux est
**structurellement inaccessible** à ce profil.

| Profil | Créneaux libres S1 | Créneaux libres S2 |
|---|---|---|
| Étudiant A+B | Ma-am · Ma-pm · Me-am · Ve-pm | Ma-am · Ma-pm · Me-am · Ve-pm |
| Étudiant A+C | Lu-pm · Ma-pm · Me-am · Ve-am | Lu-am · Ma-pm · Me-am · Me-pm |
| Étudiant B+C | Lu-am · Ma-pm · Me-am · Me-pm | Lu-pm · Ma-pm · Me-am · Ve-am |
| **Apprenti A** | **Lu-pm · Me-am** | **Lu-am · Ve-pm** |
| **Apprenti B** | **Lu-am · Ve-pm** | **Lu-pm · Me-am** |
| **Apprenti C** | **Ma-pm · Ve-am** | **Ma-pm · Ve-am** |
| Auditeur (échange) | 8 créneaux (aucune contrainte) | 8 créneaux (aucune contrainte) |

> **À retenir** : un étudiant classique a 4 créneaux libres par semestre.
> Un apprenti n'en a que **2** — il est structurellement le profil le plus
> à risque de blocage.

---

## 5. Matrice profil × bloc — la clé du diagnostic

Chaque cellule donne, pour l'offre 2026-2027, le nombre d'occurrences
accessibles au profil et, entre parenthèses, la capacité cumulée.
**`BLOQUÉ` signifie « aucune occurrence de ce bloc n'est physiquement
accessible à ce profil »** — l'algorithme n'y peut rien.

| Profil | Droit | Eco Num | SEHS | Humanités | Ouverture | TC IA | TC Optim | TC Stat | TC Sécurité |
|---|---|---|---|---|---|---|---|---|---|
| **Apprenti A FR** | BLOQUÉ | BLOQUÉ | 3 (130) | BLOQUÉ | 8 (305) | BLOQUÉ | BLOQUÉ | 2 (290) | 1 (80) |
| **Apprenti A EN** | BLOQUÉ | BLOQUÉ | 3 (130) | BLOQUÉ | 6 (220) | BLOQUÉ | BLOQUÉ | 1 (110) | 1 (80) |
| **Apprenti B FR** | 2 (260) | 1 (80) | BLOQUÉ | 3 (90) | 2 (95) | 1 (80) | 1 (40) | BLOQUÉ | 2 (160) |
| **Apprenti B EN** | 2 (260) | 1 (80) | BLOQUÉ | 3 (90) | 2 (95) | 1 (80) | BLOQUÉ | BLOQUÉ | BLOQUÉ |
| **Apprenti C FR** | 1 (50) | 2 (160) | 5 (165) | 3 (90) | 8 (284) | 2 (160) | 5 (220) | 1 (30) | 1 (80) |
| **Apprenti C EN** | 1 (50) | 2 (160) | 5 (165) | 3 (90) | 6 (204) | 2 (160) | 1 (40) | BLOQUÉ | BLOQUÉ |
| Étudiant A+B FR | 3 (310) | 3 (240) | 6 (185) | 6 (180) | 13 (524) | 2 (160) | 3 (150) | 2 (290) | 3 (240) |
| Étudiant A+B EN | 3 (310) | 3 (240) | 6 (185) | 6 (180) | 10 (389) | 2 (160) | 1 (40) | 1 (110) | 1 (80) |
| Étudiant A+C FR | 3 (310) | 2 (160) | 6 (245) | 6 (180) | 13 (474) | 2 (160) | 4 (190) | 2 (290) | 2 (160) |
| Étudiant A+C EN | 3 (310) | 2 (160) | 6 (245) | 6 (180) | 9 (309) | 2 (160) | 1 (40) | 1 (110) | 1 (80) |
| Étudiant B+C FR | 3 (310) | 3 (240) | 5 (165) | 6 (180) | 12 (454) | 2 (160) | 3 (120) | 2 (290) | 3 (240) |
| Étudiant B+C EN | 3 (310) | 3 (240) | 5 (165) | 6 (180) | 9 (319) | 2 (160) | 1 (40) | 1 (110) | 1 (80) |
| Auditeur FR | 3 (310) | 4 (320) | 9 (325) | 6 (180) | 18 (684) | 4 (320) | 6 (300) | 2 (290) | 4 (320) |
| Auditeur EN | 3 (310) | 4 (320) | 9 (325) | 6 (180) | 14 (519) | 4 (320) | 1 (40) | 1 (110) | 1 (80) |

### Ce que ce tableau révèle

- **Les apprentis A** sont bloqués sur **5 blocs sur 9** : Droit, Économie
  du numérique, Humanités, TC IA, TC Optim.
- **Les apprentis B francophones** sont bloqués sur SEHS et TC Stat.
  Les apprentis B anglophones ajoutent TC Optim et TC Sécurité — soit **4
  blocs inaccessibles**.
- **Les apprentis C** sont les mieux servis (aucun blocage pour les FR).
- **Les auditeurs** (échange) sont structurellement peu contraints, sauf
  en Optim et Sécurité s'ils sont anglophones (peu d'offre en anglais).

---

## 6. Charge accessible par profil — la question des crédits

Chaque bloc affecté représente **une période occupée**, valorisée à
**2,5 crédits**. L'objectif institutionnel est que chaque élève atteigne
**au moins 15 crédits** (soit **6 blocs**), idéalement 8 blocs.

| Profil | Blocs accessibles max | Crédits max théoriques | Cible ≥ 15 crédits |
|---|:---:|:---:|:---:|
| Étudiant A+B FR / EN | 9 | 22,5 | OK |
| Étudiant A+C FR / EN | 9 | 22,5 | OK |
| Étudiant B+C FR / EN | 9 | 22,5 | OK |
| Auditeur FR / EN | 9 | 22,5 | OK |
| **Apprenti A FR** | **4** | **10,0** | **SOUS-CHARGE** |
| **Apprenti A EN** | **4** | **10,0** | **SOUS-CHARGE** |
| Apprenti B FR | 7 | 17,5 | OK |
| **Apprenti B EN** | **5** | **12,5** | **SOUS-CHARGE** |
| Apprenti C FR | 9 | 22,5 | OK |
| Apprenti C EN | 7 | 17,5 | OK |

> **Résultat central** : **les apprentis A ne peuvent structurellement
> accéder qu'à 4 blocs (10 crédits) — 5 crédits en-dessous du minimum**.
> Les apprentis B anglophones sont à 12,5 crédits. Ces situations sont
> **impossibles à résoudre par un algorithme d'affectation** ; elles
> demandent une action côté offre.

---

## 7. Capacités agrégées par bloc

Pour chaque bloc, comparaison entre la capacité totale offerte et la
taille de la promotion (348 étudiants en 2026-2027). La capacité **hors
FISEA** est celle réellement ouverte aux non-apprentis (voir §8).

| Bloc | Occurrences | Capacité totale | Capacité hors FISEA | Surplus (hors FISEA) | Tension |
|---|:---:|:---:|:---:|:---:|:---:|
| **TC Stat** | 3 | 320 | **290** | **−58** | TENDU |
| **TC Optim** | 7 | 330 | **300** | **−48** | TENDU |
| **Droit** | 3 | 310 | 310 | −38 | TENDU |
| **TC IA** | 4 | 320 | 320 | −28 | TENDU |
| **TC Sécurité** | 4 | 320 | 320 | −28 | TENDU |
| **Eco Num** | 4 | 320 | 320 | −28 | TENDU |
| **SEHS** | 9 | 325 | 325 | −23 | TENDU |
| Humanités | 13 | 390 | 390 | +42 | OK |
| Module d'ouverture | 18 | 684 | 684 | +336 | OK |

**Sept blocs sur neuf ont une capacité insuffisante pour la promotion
entière.** Même si l'algorithme d'affectation était parfait, il resterait
un déficit de 58 places en Statistique, 48 en Optimisation, etc. Pour
atteindre 100 % d'affectations, il faut soit ouvrir des places
supplémentaires, soit ajouter des occurrences.

---

## 8. Le cas particulier FISEA (Statistiques)

Dans l'offre 2026-2027, **une seule occurrence est marquée FISEA** :
`APM_4TC03_TP` — « Statistiques (FISEA) » sur **Ma-pm**, capacité 30 places.
Elle est **exclusivement réservée aux apprentis**.

Cette réservation crée un effet de bord asymétrique :

- Sur Ma-pm (créneau universel), les apprentis A et B ne sont pas
  physiquement présents (Ma est un jour d'entreprise pour ces groupes)
  → **seuls les apprentis C peuvent y assister**.
- Les apprentis A francophones peuvent aller aux Stat classiques
  (Me-am, capacité 290) : ils passent.
- **Les apprentis B ne peuvent aller NI aux Stat classiques
  (Me = jour d'entreprise), NI aux Stat FISEA (Ma = jour d'entreprise).
  Ils n'ont AUCUN cours de Statistique accessible.**

Une **seconde occurrence FISEA de Statistique**, placée sur un créneau
compatible groupes A/B (typiquement Lu-pm en S1 pour les apprentis A, ou
Ve-pm pour les apprentis B) résoudrait ce blocage.

---

## 9. Récapitulatif des actions recommandées

Priorité **HAUTE** — débloque des situations impossibles :

1. **Créer une occurrence de Statistique accessible aux apprentis A et B**
   (créneau à choisir dans leurs demi-journées d'école, hors Me-am déjà
   utilisée par les Stat classiques). Impact : ~10 apprentis débloqués.
2. **Créer des occurrences apprentis pour les blocs actuellement bloqués** :
   Droit, Eco Num, IA, Optim, Humanités — au moins pour les apprentis A
   (5 blocs manquants) et B EN (2 blocs manquants).
3. **Réviser le calendrier des jours d'entreprise** pour que les apprentis
   aient accès à au moins 4 créneaux libres par semestre (ce que les
   étudiants classiques ont naturellement).

Priorité **MOYENNE** — ferme le trou capacitaire :

4. **+58 places en Statistique** (typiquement en agrandissant la salle
   `APM_4TC01_TP` ou en ouvrant une 4ᵉ occurrence sur Ma-pm ou Me-am).
5. **+48 places en Optimisation** (répartir sur les 7 occurrences existantes
   ou ajouter une 8ᵉ).
6. **+30 à +40 places** sur chaque bloc restant tendu (Droit, IA, Sécurité,
   Eco Num, SEHS).

Avec les priorités HAUTE traitées, les apprentis atteindront la cible de
15 crédits. Avec les MOYENNES, l'algorithme atteindra 100 % d'affectations.

---

## 10. Reproduction de l'analyse

Toutes les données de ce document sont générées par le script
[`tools/analyse_structurelle.py`](../tools/analyse_structurelle.py).
Pour rejouer l'analyse sur une autre année :

```bash
python -m tools.analyse_structurelle data/2026
```

Le script énumère 14 profils structurels, calcule leurs créneaux libres
par semestre, et croise avec l'offre de cours pour produire les quatre
tableaux ci-dessus.

Aucune référence aux vœux réels des élèves n'est faite : le diagnostic
est **portable** d'une année à l'autre à condition que la structure des
créneaux et des blocs ne change pas.
