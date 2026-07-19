# Cahier des charges — Affectation des élèves aux cours électifs (Télécom Paris, 2ᵉ année)

> **Nature du document.** Ceci est un document de cadrage, rédigé pour être lu
> aussi bien par une personne de la scolarité que par un développeur. Il décrit,
> dans l'ordre : le contexte, le vocabulaire, le problème, les données, la
> typologie des étudiants, la structure du temps (créneaux), la façon dont un
> profil d'étudiant engendre des choix forcés, les contraintes, les propriétés
> attendues de la solution, l'objectif et ses métriques, la sortie attendue, les
> points de vigilance sur les données, puis un panorama de méthodes de résolution
> éprouvées. L'objectif final est de permettre l'écriture d'un code **court,
> lisible et facile à déboguer** (idéalement un fichier de prétraitement et un
> fichier par algorithme, de moins de 200 lignes chacun), exécuté **une fois par
> an**.

---

## 1. Contexte

Chaque année, les élèves de deuxième année doivent constituer leur emploi du temps
en s'inscrivant à un ensemble de cours obligatoires appelés le **tronc commun**.
Ce tronc commun n'est pas un bloc figé : pour la plupart des matières, l'école
propose **plusieurs versions du même enseignement** — à des horaires différents,
dans des langues différentes (français ou anglais), parfois avec une pédagogie
différente (cours théorique ou travaux pratiques). L'élève ne choisit donc pas
seulement *quoi* étudier (le programme le lui impose en grande partie), mais
surtout *quand* et *dans quelle version* il suivra chaque matière.

L'enjeu de l'école est double. D'une part, elle veut **répartir les élèves sur
toute la semaine** plutôt que de les concentrer tous sur un même créneau : cette
année, un engorgement s'est produit parce que trop d'élèves se retrouvaient au
même moment, saturant les salles de travaux pratiques et dépassant les capacités
d'accueil. D'autre part, elle veut que cette répartition soit **la plus
satisfaisante possible pour les élèves** : autant que faire se peut, chacun doit
obtenir les versions de cours qu'il préfère.

Le résultat de ce travail sera utilisé par le **coordinateur des études**, qui
n'est pas informaticien. Il doit pouvoir, à travers une interface simple, déposer
les fichiers fournis par la scolarité, lancer le calcul, **visualiser le résultat
pour le valider** (ou le rejeter), puis récupérer un fichier qu'il réinjectera
dans **Synapse**, le système d'information de la scolarité. L'algorithme ne
communique jamais directement avec Synapse : il lit des fichiers, calcule, et
écrit des fichiers.

L'échéance est la **campagne d'inscription pédagogique de fin août / début
septembre**. Le temps de calcul acceptable est de l'ordre de **quelques minutes**,
et en tout état de cause **inférieur à une heure**.

---

## 2. Vocabulaire

Pour éviter toute ambiguïté, voici les termes employés dans ce document.

- **UE (unité d'enseignement)** : une matière au sens du programme, identifiée par
  un code (par exemple « Optimisation continue »). C'est l'objet que l'élève
  *classe* dans ses vœux.
- **Occurrence** : une **séance concrète** d'une UE, avec un horaire précis, une
  langue et une capacité. Une même UE peut avoir **plusieurs occurrences** : par
  exemple « Optimisation » peut exister en version française le lundi matin, en
  version anglaise le mardi après-midi, et en version travaux pratiques le
  vendredi matin. **C'est à une occurrence que l'élève est finalement affecté**,
  pas à une UE abstraite.
- **Bloc** (ou **catégorie**) : la famille à laquelle appartient une UE
  (Statistiques, Optimisation, IA, Sécurité, Modules d'ouverture, Droit, Économie
  du numérique, SEHS, Humanités…). Le programme impose de valider **exactement une
  UE par bloc obligatoire**.
- **Période** : l'année est découpée en quatre périodes. Les deux premières (P1,
  P2) forment le **semestre 1** ; les deux dernières (P3, P4) forment le
  **semestre 2**. Chaque occurrence a lieu dans une période donnée.
- **Créneau** : une **demi-journée** de la semaine (par exemple « lundi matin »,
  noté Lu-am, ou « mardi après-midi », noté Ma-pm). Chaque occurrence occupe un
  créneau. Deux occurrences sur le même créneau, à la même période, sont
  **incompatibles** : un élève ne peut pas suivre les deux.
- **Filière** : le parcours de spécialisation de l'élève (par exemple « Data
  Science & IA »). Chaque filière **réserve des créneaux fixes** dans la semaine
  pour ses propres cours ; l'élève n'est donc **pas disponible** sur ces créneaux
  pour un cours du tronc commun. Un élève classique appartient à **deux**
  filières ; un apprenti à **une** ; un étudiant d'échange à **aucune**.
- **Campagne / demande** : dans Synapse, une *campagne* d'inscription regroupe
  plusieurs *demandes*. Une **demande** correspond à un classement à effectuer par
  l'élève (par exemple « classez les modules d'ouverture de 1 à 10 »). Dans notre
  problème, **une demande correspond à un bloc obligatoire** : il y a donc autant
  de demandes que de blocs à pourvoir.

---

## 3. Le problème à résoudre

En une phrase :

> **Affecter chaque élève à une occurrence de chacun des blocs qu'il doit suivre,
> en respectant ses indisponibilités (créneaux de filière, jours bloqués),
> sa langue, son régime et les capacités des salles, de manière à ce que
> l'ensemble des élèves obtienne le plus possible ses cours préférés.**

Deux idées sont essentielles pour bien comprendre la nature du problème, et elles
corrigent une intuition trop simple selon laquelle « certaines matières seraient
imposées et d'autres au choix ».

**Première idée — le choix existe partout, par défaut.** Il n'y a pas de matière
« sans choix » par nature. Pour *chaque* bloc, l'élève classe les UE qui l'y
intéressent, et le système lui cherche la meilleure occurrence possible. Même une
matière apparemment simple comme les statistiques peut exister en version
française et en version anglaise sur le même créneau : un élève francophone a donc
un vrai choix (la langue), que rien ne lui retire *a priori*.

**Seconde idée — le caractère « forcé » est une conséquence, pas une règle.** Un
choix ne devient « forcé » que lorsque, **pour cet élève précis**, tous les
filtres (créneaux occupés par sa filière, langue imposée, jours bloqués s'il est
apprenti) ne laissent survivre **qu'une seule occurrence admissible** dans un bloc
donné. Le forçage émerge donc de la **rencontre entre un profil et l'offre de
cours**, et il varie d'un élève à l'autre. C'est ce mécanisme, détaillé au §6, qui
fait tout le sel du problème.

---

## 4. Les données à disposition

Trois fichiers CSV extraits de Synapse (séparateur `;`). Les colonnes ci-dessous
sont celles des fichiers réels de l'année 2026-2027. Le point d'entrée côté école
pour toute question d'extraction est **Alexia**.

### 4.1 La liste des élèves

Colonnes : `Id Personne ; Nom ; Prénom ; N° INE ; Diplôme ; Cursus ; Régime
d'inscription ; Francophone ; Filières`.

- Environ 348 élèves.
- **Diplôme** : soit **ING** (élève ingénieur, cursus de 24 ou 36 mois), soit
  **PEI** (programme d'échange international, cursus d'un ou deux semestres).
- **Régime d'inscription** : `Étudiant`, `Apprenti`, ou
  `Auditeur libre` (ce dernier pour les élèves d'échange).
- **Francophone** : `OUI` ou `NON`. Un élève marqué `NON` est traité comme
  **anglophone**.
- **Filières** : les codes des filières de l'élève, séparés par le symbole `$$`
  (par exemple `DSAI$$MACS`). Un élève classique en a deux ; un apprenti une ; un
  élève d'échange aucune.

### 4.2 La liste des cours (occurrences)

Colonnes : `Idoccur ; Idue ; Codeue ; Intitulé occurrence ; Période ; Bloc ;
Créneau prédéfini ; Nb inscrits ; Effectif min ; Effectif max ; Langues ; FISEA`.

- Chaque ligne est **une occurrence** ; l'identifiant `Idue` regroupe les
  occurrences d'une même UE.
- **Période** : `S1-P1`, `S1-P2`, `S2-P3`, `S2-P4`.
- **Bloc** : la catégorie (voir §2).
- **Créneau prédéfini** : la demi-journée (Lu-am, Ma-pm, Me-am…). **Il peut être
  vide** pour certaines occurrences dont l'horaire est encore souple (par exemple
  des cours d'Humanités annoncés « en P3 ou en P4 »), qu'il faudra donc placer.
- **Nb inscrits / Effectif min / Effectif max** : la capacité. Le nombre de places
  encore disponibles vaut *effectif maximal moins nombre déjà inscrits*.
  En-dessous de l'effectif minimal, l'occurrence risque d'être annulée.
- **Langues** : `Français` ou `Anglais`.
- **FISEA** : `O` marque une occurrence réservée aux **apprentis**.

### 4.3 La liste des filières et de leurs créneaux

Colonnes : `Id parcours ; Code parcours ; Créneau (groupe A/B/C) ; Intitulé ;
puis, pour chaque période, les deux demi-journées réservées`.

- Chaque filière appartient à un **groupe de créneau A, B ou C** et **réserve deux
  demi-journées par période** pour ses propres cours. Ce sont précisément les
  moments où l'élève de cette filière **n'est pas disponible** pour un cours du
  tronc commun.

### 4.4 Les échanges avec Synapse (à confirmer avec Alexia)

- **En sortie de campagne** (les vœux des élèves) : `id élève ; id campagne ; id
  demande ; choix 1 ; choix 2 ; …` — un classement par demande, c'est-à-dire par
  bloc. [Il se pourrait que pour l'instant les demandes ne soient par formulées de cette façon là, il sera alors il faudra créé un csv temporaire à partir des donénes disponibles, qui respecterait ce format]
- **En import de retour vers Synapse** (le résultat) : pour chaque demande,
  `id élève ; id campagne ; id demande ; id occurrence`.

---

## 5. La typologie des étudiants : ce qu'un élève peut être, ou ne pas être

Un même élève est décrit par **plusieurs caractéristiques indépendantes**, qui se
combinent. Bien comprendre ces combinaisons est indispensable, car ce sont elles
qui déterminent les contraintes qui pèseront sur lui.

### 5.1 Les quatre caractéristiques d'un profil

1. **Le régime** : `Étudiant`, `Apprenti` ou `Auditeur
   libre` (élève d'échange). Un élève a **un seul** régime.
2. **La langue** : francophone ou anglophone. Un élève est **soit l'un, soit
   l'autre**, jamais les deux à la fois.
3. **Le nombre de filières** : zéro, une, ou deux (exceptionnellement trois).
4. **Le ou les groupes de créneau** (A, B, C) auxquels ses filières appartiennent,
   qui déterminent ses indisponibilités horaires.

### 5.2 Les combinaisons possibles et impossibles

Ces caractéristiques ne sont pas toutes libres de se combiner. En pratique :

- Un **élève classique** (régime « Étudiant ») a **deux filières**. Ses deux
  filières appartiennent en général à deux groupes de créneau différents, ce qui
  détermine ses créneaux occupés (voir §6).
- Un **apprenti** a **une seule filière**, et **en plus** des jours entiers
  bloqués dans la semaine (il est en entreprise). Il est donc, mécaniquement, le
  profil le **plus contraint** en matière de disponibilité.
- Un **élève d'échange** (auditeur libre, cursus PEI) n'a **aucune filière** : il
  n'a donc pas de créneau réservé par une spécialisation. En revanche, il est
  très souvent **anglophone**, ce qui restreint fortement les cours qu'il peut
  suivre.
- La **langue est indépendante du régime** : on peut en théorie être apprenti et
  anglophone, ou étudiant classique et anglophone. Dans les données observées,
  tous les apprentis se trouvent être francophones et tous les anglophones se
  trouvent être soit des étudiants classiques, soit des élèves d'échange. Il y a aussi des auditeurs libres qui sont francophones — Le
  système **ne doit pas supposer** cette coïncidence : il doit accepter n'importe
  quelle combinaison.
- On ne peut **pas** être francophone *et* anglophone simultanément : c'est un
  drapeau unique. De même, on n'a **pas** deux régimes à la fois.
- Un élève d'échange n'a **pas** de filière ; un apprenti n'en a **pas** deux.
  Ce sont des règles de gestion, qu'il faut respecter mais aussi vérifier (les
  données peuvent contenir des exceptions, cf. §11).

### 5.3 Pourquoi cette typologie compte

Chaque caractéristique retire des possibilités à l'élève :

- **être anglophone** retire les cours en français (mais seulement au premier
  semestre — voir §7) ;
- **être apprenti** retire des jours entiers de la semaine ; (les jours qui ne concernent pas la filiere de l'apprenti)
- **avoir des filières** retire les créneaux que ces filières réservent ;
- **cumuler deux filières** retire l'union des créneaux des deux.

Plus un élève cumule de caractéristiques restrictives, plus le nombre
d'occurrences qui lui restent accessibles diminue — jusqu'au point où, dans
certains blocs, il ne lui reste **qu'une seule possibilité**. C'est là que naît le
« choix forcé ».

---

## 6. La structure du temps : périodes et créneaux

C'est le cœur des contraintes, et le point le plus important à bien saisir. Tout
tourne autour d'une idée simple : **un élève ne peut suivre un cours que sur un
créneau où il est libre**, et il n'est libre que là où aucune de ses filières
(ni, le cas échéant, ses jours d'apprentissage) ne l'occupe déjà.

### 6.1 Le découpage de la semaine

La semaine utile est découpée en **demi-journées** : lundi matin, lundi
après-midi, mardi matin, mardi après-midi, mercredi matin, mercredi après-midi,
vendredi matin, vendredi après-midi. (Le jeudi n'accueille pas de cours de tronc
commun ; il sert de respiration et de jour d'entreprise pour les apprentis.)
Chaque occurrence de cours se tient sur **une** de ces demi-journées, à **une**
période donnée.

### 6.2 Ce que chaque groupe de filière réserve

Chaque groupe de créneau réserve deux demi-journées par période. Les trois groupes
sont construits pour **ne pas se chevaucher** entre eux au sein d'une même
période, et les groupes A et B sont même conçus en **miroir** l'un de l'autre
(quand A occupe le début de semaine, B occupe la fin, et inversement d'un semestre
à l'autre). Le groupe C occupe les mêmes deux demi-journées à toutes les périodes.

De façon résumée, sur un semestre :

| Groupe | Demi-journées réservées (semestre 1) | Demi-journées réservées (semestre 2) |
|---|---|---|
| A | lundi matin, mercredi après-midi | lundi après-midi, vendredi matin |
| B | lundi après-midi, vendredi matin | lundi matin, mercredi après-midi |
| C | mardi matin, vendredi après-midi | mardi matin, vendredi après-midi |

### 6.3 La propriété fondamentale : deux créneaux libres pour tout le monde

Si l'on superpose les trois groupes, on constate que **deux demi-journées ne sont
jamais réservées par aucune filière** : le **mardi après-midi** et le **mercredi
matin**. Ces deux créneaux sont donc **libres pour absolument tous les élèves**,
quelle que soit leur filière.

C'est une propriété structurante : les cours réellement communs à toute la
promotion (typiquement les statistiques) sont naturellement placés sur ces deux
créneaux universels, car ce sont les seuls où l'on est certain que chacun peut
être présent. À l'inverse, une occurrence placée sur un autre créneau (disons le
lundi matin) ne sera accessible **qu'aux élèves dont aucune filière n'occupe le
lundi matin**.

### 6.4 Combien de créneaux reste-t-il à chaque élève ?

Pour un élève classique à deux filières, l'ensemble des créneaux occupés est
l'**union** des créneaux de ses deux filières. Quelques exemples au premier
semestre :

| Profil de filières | Demi-journées occupées | Demi-journées libres restantes |
|---|---|---|
| A + B | lundi matin, mercredi après-midi, lundi après-midi, vendredi matin | mardi matin, **mardi après-midi**, **mercredi matin**, vendredi après-midi |
| A + C | lundi matin, mercredi après-midi, mardi matin, vendredi après-midi | lundi après-midi, **mardi après-midi**, **mercredi matin**, vendredi matin |
| B + C | lundi après-midi, vendredi matin, mardi matin, vendredi après-midi | lundi matin, **mardi après-midi**, **mercredi matin**, mercredi après-midi |

On observe deux choses. D'abord, **tout élève à deux filières dispose exactement
de quatre demi-journées libres** au premier semestre, dont **toujours** le mardi
après-midi et le mercredi matin (les deux créneaux universels), plus deux autres
qui dépendent de sa combinaison. Ensuite, un **apprenti** (une seule filière, mais
des jours d'entreprise bloqués) peut se retrouver avec un nombre de créneaux libres
**encore plus faible**, selon les jours où son entreprise le retient.

### 6.5 Les règles de temps qui en découlent

De cette structure naissent trois contraintes horaires précises :

1. **Un cours ne peut être suivi que sur un créneau libre pour l'élève.** Toute
   occurrence dont le créneau est réservé par l'une de ses filières lui est
   inaccessible.
2. **Deux cours d'un même élève ne peuvent pas tomber sur le même créneau à la
   même période.** L'emploi du temps final doit être sans collision.
3. **La charge de chaque période doit rester raisonnable.** Le programme prévoit un
   nombre de cours par période encadré (de l'ordre de deux à trois) : on ne peut
   ni entasser toutes les matières sur une période, ni en laisser une vide. Cette
   règle **couple les blocs entre eux** : le choix d'occurrence dans un bloc influe
   sur les créneaux encore disponibles pour les autres.

---

## 7. Comment un profil engendre des choix forcés

Nous pouvons maintenant assembler les pièces. Pour un élève donné et un bloc donné,
on part de **toutes** les occurrences de ce bloc, puis on retire successivement :

1. celles dont **le créneau est occupé** par l'une de ses filières ;
2. celles qui tombent sur un **jour bloqué** (uniquement s'il est apprenti) ;
3. celles dont **la langue ne lui convient pas** — et ce filtre a une portée très
   précise :
   - il ne s'applique **qu'aux élèves anglophones**, et **uniquement au premier
     semestre** : un anglophone ne peut y suivre que des cours en anglais ;
   - **les francophones ne sont jamais restreints** sur la langue : ils peuvent
     suivre indifféremment un cours en français ou en anglais ;
   - **au second semestre, plus personne** n'est restreint sur la langue, pas même
     les anglophones.

Ce qui reste après ces trois filtres est l'ensemble des occurrences **réellement
accessibles** à l'élève dans ce bloc. Trois cas se présentent :

- **Plusieurs occurrences restantes** → l'élève a un **vrai choix**, et son
  classement de vœux départage.
- **Une seule occurrence restante** → le choix est **forcé** : quelle que soit sa
  préférence, il ne peut aller que là.
- **Aucune occurrence restante** → **situation problématique** : l'élève ne peut
  valider ce bloc. Il faudra le signaler explicitement (voir §10) et sans doute
  ajuster l'offre ou traiter le cas à la main.

### 7.1 Deux exemples concrets

**Exemple A — le bloc « Sécurité » au premier semestre.** Ce bloc est proposé en
français (plusieurs occurrences, réparties sur différentes demi-journées) et en
anglais (une occurrence, le mercredi matin).

- Un **élève anglophone** ne peut, au premier semestre, suivre que l'anglais : il
  est donc **forcé** sur l'unique occurrence anglaise du mercredi matin. Comme ce
  créneau est universellement libre, l'affectation est toujours possible — mais il
  n'a aucun choix.
- Un **élève francophone**, lui, peut suivre **soit** l'une des versions
  françaises (sur les demi-journées où sa filière le laisse libre), **soit** la
  version anglaise. Il a donc un choix riche, que son classement départage.

**Exemple B — un apprenti très contraint.** Un apprenti n'ayant qu'une filière du
groupe C (occupé mardi matin et vendredi après-midi) *et* dont l'entreprise bloque
le vendredi se retrouve avec très peu de demi-journées libres. Dans un bloc dont
les occurrences ne tomberaient que sur le vendredi après-midi et le mardi matin,
il pourrait ne lui rester **qu'une seule** possibilité — un choix forcé — voire
**aucune**, ce qui devrait alors être remonté comme une alerte.

### 7.2 La leçon à retenir

Le « forçage » n'est donc **jamais attaché à une matière** (« les stats seraient
imposées, les modules d'ouverture au choix »). Il est attaché à la **rencontre
entre un profil et l'offre** : le même bloc peut être un choix libre pour l'un et
une obligation de fait pour l'autre. Concrètement, ce sont surtout **les élèves les
plus contraints** — anglophones au premier semestre, apprentis, élèves cumulant
deux filières « gourmandes » en créneaux — qui accumulent les choix forcés, tandis
qu'un francophone à filières peu contraignantes garde presque partout un vrai choix.

---

## 8. Les contraintes

### 8.1 Contraintes dures (à respecter impérativement)

1. **Compatibilité horaire.** Aucun cours affecté à un élève ne peut tomber sur un
   créneau réservé par l'une de ses filières, ni sur un jour bloqué s'il est
   apprenti ; et deux cours d'un même élève ne peuvent partager le même créneau à
   la même période.
2. **Complétude du cursus.** L'élève reçoit **exactement une occurrence par bloc
   obligatoire** qui le concerne, au bon semestre.
3. **Charge par période encadrée.** Le nombre de cours par période reste dans les
   bornes prévues (de l'ordre de deux à trois).
4. **Langue.** Un anglophone ne suit, au premier semestre, que des cours en
   anglais ; les francophones ne sont pas restreints ; au second semestre, la
   contrainte de langue tombe pour tous.
5. **Capacité des cours.** Pour chaque occurrence, le nombre d'élèves affectés,
   ajouté aux éventuels déjà-inscrits, ne dépasse pas l'effectif maximal.
6. **Affectations imposées par le régime.** Les apprentis relèvent d'occurrences
   qui leur sont réservées (marquées FISEA) et de disponibilités réduites.
7. **Unicité.** Un élève n'est affecté qu'à une seule occurrence d'une même UE.

### 8.2 Contraintes souples et priorités (à optimiser, sans garantie absolue)

1. **Priorité aux anglophones sur les cours en anglais.** Un élève international
   doit pouvoir obtenir une place en anglais ; il faut lui en réserver l'accès en
   priorité, plutôt que de le laisser « repoussé » par le jeu de l'algorithme.
2. **Respect de l'effectif minimal.** On cherche à éviter les occurrences
   sous-remplies, qui risquent l'annulation, quitte à regrouper les élèves.
3. **Éventuels profils prioritaires** (par exemple les redoublants) : techniquement
   envisageable, mais **non retenu par défaut**, faute de justification claire.

---

## 9. Les propriétés attendues de la solution

Au-delà du simple respect des contraintes, on souhaite que l'affectation possède
certaines **qualités**, qui font qu'elle sera perçue comme juste et acceptable.

- **Efficacité globale** : on cherche à maximiser la satisfaction de l'ensemble,
  pas celle d'un individu isolé. Il est acceptable qu'un élève donné n'ait pas son
  tout premier choix si cela permet à plusieurs autres d'avoir les leurs.
- **Absence de gâchis (efficacité de Pareto)** : on ne veut pas d'une affectation
  qu'on pourrait améliorer pour un élève sans en léser aucun autre. S'il reste une
  place dans un cours qu'un élève préfère à celui qu'il a reçu, et que personne
  n'en pâtit, l'échange devrait avoir lieu.
- **Équité** : à profil comparable, deux élèves devraient être traités de façon
  comparable ; aucun groupe (une filière, un régime, une langue) ne doit être
  systématiquement défavorisé. On veillera aussi au sort du **moins bien loti**,
  et pas seulement à la moyenne.
- **Robustesse à la déclaration** : dans la mesure du possible, un élève ne devrait
  **pas** avoir intérêt à mentir sur ses préférences pour obtenir un meilleur
  résultat. Un mécanisme où déclarer ses vrais vœux est la meilleure stratégie est
  préférable, car il est à la fois plus juste et plus simple à expliquer.
- **Transparence et traçabilité** : pour chaque élève, on doit pouvoir expliquer
  *pourquoi* il a obtenu telle occurrence, et surtout *pourquoi*, le cas échéant,
  il n'a rien obtenu. Une décision incompréhensible est une décision contestable.
- **Stabilité modérée** : une petite modification de l'entrée (un élève ajouté, une
  capacité corrigée) ne devrait pas bouleverser toute l'affectation.

---

## 10. Objectif et métriques de satisfaction

**L'objectif** est de maximiser la satisfaction globale de la promotion, sous les
contraintes du §8 et en visant les propriétés du §9.

Pour piloter et juger la qualité d'un résultat, on mesure notamment :

| Indicateur | Ce qu'il exprime |
|---|---|
| **Rang obtenu** par élève | la position, dans son propre classement, du cours qu'il a reçu (1 = son premier choix). C'est la mesure la plus parlante. |
| **Distribution des rangs** | la proportion d'élèves ayant obtenu leur 1ᵉʳ choix, leur 2ᵉ, …, leur n-ième. C'est le tableau de bord principal. |
| **Satisfaction moyenne** | un résumé chiffré (par exemple la moyenne d'un score décroissant avec le rang). |
| **Sort du moins bien loti** | le plus mauvais rang servi, pour repérer les élèves sacrifiés. |
| **Taux de non-affectés** | la part d'élèves qui n'ont rien pu obtenir sur un bloc. |
| **Équité entre groupes** | la satisfaction moyenne comparée par filière, par régime, par langue. |
| **Taux de remplissage** | l'occupation de chaque occurrence, avec alerte sous l'effectif minimal. |

---

## 11. La sortie attendue

Le système produit deux choses.

### 11.1 Le fichier d'affectation (à réinjecter dans Synapse)

Pour chaque bloc et chaque élève : `id élève ; id campagne ; id demande ; id
occurrence`. C'est le fichier que le coordinateur des études déposera dans Synapse
pour rendre les inscriptions effectives.

### 11.2 Le rapport d'analyse (pour validation humaine avant réinjection)

Un document **lisible par un non-technicien**, qui permet de décider si
l'affectation est acceptable. Il contient au minimum :

- **La distribution des rangs obtenus** : combien d'élèves ont eu leur premier
  choix, leur deuxième, et ainsi de suite — présentée sous forme d'histogramme.
- **La liste des élèves non affectés, avec la cause explicite** de chaque échec.
  C'est un point essentiel de traçabilité. Les causes typiques sont :
  - aucun de ses vœux n'était compatible avec ses créneaux de filière ;
  - tous ses vœux accessibles étaient déjà **complets** (capacité atteinte) ;
  - conflit de langue (un anglophone n'avait classé aucune occurrence en anglais) ;
  - une liste de vœux trop courte pour absorber la concurrence.
- **Le remplissage de chaque occurrence** (places occupées sur places offertes),
  avec un signalement des occurrences sous leur effectif minimal.
- **Les éventuels dépassements de capacité** (qui, en principe, ne devraient pas
  exister si les contraintes sont respectées).
- **Les indicateurs d'équité** par groupe (§10).

Le code qui produit ce rapport est **séparé** de celui qui calcule l'affectation :
il se contente de relire la sortie et les données d'entrée pour en tirer des
statistiques et des explications.

---

## 12. Points de vigilance sur les données

Ces points doivent être clarifiés avec Alexia avant toute mise en production.

- **Vœux au niveau UE ou occurrence ?** Synapse fait probablement classer des UE,
  alors que l'affectation se fait à l'occurrence. La règle de passage de l'un à
  l'autre doit être définie.
- **Un seul classement, ou un classement par demande ?** Le code actuel n'utilise
  **qu'un seul classement global** des UE, réutilisé pour tous les blocs, alors que
  Synapse prévoit **un classement distinct par demande**. Cet écart de
  modélisation doit être tranché : veut-on un ordre de préférence unique, ou des
  préférences propres à chaque bloc ?
- **Codes de filière sans créneau connu.** Certains codes présents chez les élèves
  n'apparaissent pas dans le fichier des filières (et l'on rencontre même de rares
  élèves à trois filières). Sans créneau associé, on ne peut pas calculer leurs
  indisponibilités : Alexia doit fournir le mapping complet.
- **Incohérences de période.** Quelques occurrences affichent une période qui
  contredit leur intitulé ; il faut trancher au cas par cas.
- **Places déjà occupées.** Dans l'extrait fourni, aucune occurrence n'a de
  pré-inscrits, mais le code **doit** savoir gérer des places déjà prises (capacité
  résiduelle).
- **Créneaux vides.** Certaines occurrences n'ont pas encore d'horaire fixé ; il
  faut décider comment les placer (ou les traiter comme flexibles).
- **Élèves d'échange.** Sans filière et le plus souvent anglophones, ils forment un
  cas particulier qu'il faut traiter explicitement.
- **Données personnelles.** Même anonymisées ici, ces données restent sensibles :
  prudence dans leur manipulation et leur stockage.

---

## 13. Panorama des méthodes de résolution

Le problème se ramenant, une fois les forçages appliqués, à une **affectation par
bloc sous contrainte de capacité**, plusieurs approches simples et éprouvées
existent. Pour chacune : le principe, des cas réels du **même type de problème**,
une ou deux bibliothèques prêtes à l'emploi, et la forme des données à lui fournir.

### 13.1 Programmation linéaire en nombres entiers (MIP)

- **Principe.** On décrit chaque affectation possible par une variable « oui/non »
  (cet élève dans cette occurrence). On maximise la somme des satisfactions, sous
  les contraintes du §8 traduites en inéquations. Le solveur trouve l'optimum
  exact.
- **Cas réels.** Approche classique et abondamment documentée pour l'affectation de
  cours et la confection d'emplois du temps universitaires.
- **Bibliothèques.** Google **OR-Tools** (module CP-SAT), **PuLP** (avec le solveur
  gratuit CBC), **python-mip** ; solveurs commerciaux Gurobi ou CPLEX (licences
  académiques).
- **Entrée.** Une table de « poids de satisfaction » par (élève, occurrence),
  dérivée des rangs de vœux, et la liste des occurrences accessibles à chaque élève
  (après application des filtres du §7).
- **Atout.** Le plus flexible : ajouter une règle revient à ajouter une ligne de
  contrainte.

### 13.2 Flot de coût minimum

- **Principe.** On représente chaque bloc comme un réseau : une source alimente les
  élèves, chaque élève se relie aux occurrences qui lui sont accessibles (avec un
  coût égal au rang du vœu), et chaque occurrence se relie à un puits avec une
  capacité égale à ses places disponibles. Le flot le moins coûteux donne
  l'affectation optimale du bloc.
- **Cas réels.** Affectation de places sous capacité (choix d'établissement,
  attribution de salles).
- **Bibliothèques.** **NetworkX** (fonction de flot de coût minimum), OR-Tools
  (`SimpleMinCostFlow`), SciPy.
- **Entrée.** La liste des liaisons (élève, occurrence, coût = rang, capacité).
- **Atout.** Exact, très rapide, facile à déboguer ; idéal lorsqu'un seul bloc à
  choix domine.

### 13.3 Affectation bipartie (algorithme hongrois)

- **Principe.** Lorsqu'il s'agit d'affecter exactement un cours par bloc et que les
  capacités sont simples, on est dans un problème d'affectation classique.
- **Cas réels.** Appariement un-à-un standard.
- **Bibliothèques.** **SciPy** (`linear_sum_assignment`).
- **Entrée.** Une matrice de coûts élève × occurrence.
- **Limite.** Ne gère pas nativement des cours accueillant plusieurs élèves : dès
  qu'une occurrence a une capacité supérieure à un, préférer le flot de coût
  minimum (§13.2).

### 13.4 Acceptation différée (Gale-Shapley, côté élève)

- **Principe.** Les élèves « proposent » leurs vœux dans l'ordre ; chaque
  occurrence accepte provisoirement les meilleurs candidats selon sa capacité et
  une éventuelle priorité (par exemple la priorité anglophone), et libère les
  autres, jusqu'à stabilisation.
- **Cas réels.** Affectation scolaire à grande échelle (systèmes de choix d'école
  de plusieurs grandes villes), admissions universitaires.
- **Bibliothèques.** Le paquet Python **`matching`** (variante « hôpitaux /
  internes »), son équivalent R `matchingR`.
- **Entrée.** Les listes de vœux des élèves, les capacités, et les priorités
  éventuelles par occurrence.
- **Atout.** Robuste à la déclaration (déclarer ses vrais vœux est optimal pour
  l'élève) et gère naturellement la priorité anglophone.

### 13.5 A-CEEI (Course Match) — l'approche de l'implémentation actuelle

- **Principe.** On simule un marché fictif : chaque élève reçoit un budget quasi
  identique et « achète » son meilleur emploi du temps complet ; les prix des cours
  sont ajustés jusqu'à l'équilibre entre offre et demande. Cette approche offre des
  garanties d'équité fortes (personne n'envie durablement le panier d'un autre).
- **Cas réels.** Déployé pour l'attribution des cours à la Wharton School
  (« Course Match »).
- **Bibliothèques.** **`fairpyx`** (implémente Course-Match et d'autres mécanismes
  d'allocation équitable de cours).
- **Entrée.** Les valeurs attribuées par chaque élève aux paniers de cours, et les
  capacités.
- **Situation.** Pertinent si l'on veut traiter **plusieurs blocs comme un tout
  cohérent** et viser des garanties d'équité fortes ; plus lourd que les approches
  précédentes pour un problème qui se décompose largement bloc par bloc.

### 13.6 Dictateur en série aléatoire — la référence simple

- **Principe.** On tire les élèves dans un ordre aléatoire ; chacun, à son tour,
  prend son meilleur vœu encore disponible.
- **Cas réels.** Référence standard en allocation équitable.
- **Bibliothèques.** Aucune nécessaire (une trentaine de lignes).
- **Entrée.** Les listes de vœux et les capacités.
- **Atout.** Très simple, robuste à la déclaration, équitable « en espérance »
  grâce au tirage ; sert de point de comparaison pour mesurer l'apport des
  méthodes plus élaborées.

---

## 14. Recommandation de mise en œuvre

L'architecture visée tient en trois fichiers courts et indépendants.

1. **Le prétraitement** lit les trois fichiers, calcule pour chaque filière les
   créneaux qu'elle occupe, en déduit pour **chaque élève** l'ensemble des
   occurrences accessibles par bloc (en appliquant les filtres du §7 : créneaux,
   jours bloqués, langue), applique les affectations imposées par le régime, et
   produit une structure simple : pour chaque élève et chaque bloc, la liste
   ordonnée de ses occurrences accessibles.
2. **Le solveur** résout l'affectation. On recommande de commencer par le **flot de
   coût minimum par bloc** (§13.2) ou par un **programme en nombres entiers global**
   (§13.1), tous deux exacts et lisibles, en gardant le dictateur en série
   aléatoire (§13.6) comme référence de contrôle.
3. **Le rapport** relit l'affectation et les données pour produire les métriques du
   §10 et le rapport du §11, y compris les causes de non-affectation.

Le message d'ensemble : la difficulté de ce projet **n'est pas algorithmique**.
Sur environ 350 élèves et une soixantaine d'occurrences, n'importe laquelle des
méthodes ci-dessus s'exécute en quelques secondes. La vraie difficulté est dans le
**prétraitement correct des contraintes** — créneaux de filière, jours
d'apprentissage, règle de langue, capacités résiduelles — et dans la **clarté des
explications** fournies en sortie. C'est là que doivent porter le soin et les
tests, et c'est pourquoi les points de vigilance du §12 doivent être levés avec la
scolarité avant toute mise en production.
```
