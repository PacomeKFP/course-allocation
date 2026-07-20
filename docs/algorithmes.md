# Panorama pédagogique des algorithmes d'affectation

> **Public** : étudiant, enseignant, encadrant — public académique non
> spécialiste en optimisation combinatoire.
>
> **Contenu** : pour chaque algorithme implémenté, son principe, sa
> motivation, ses forces et ses faiblesses, avec les références de la
> littérature qui les fondent.

Le problème d'affectation étudiants ↔ cours à Télécom Paris est un cas
particulier de deux littératures qui se recoupent :
d'un côté la **théorie du matching** (économie et théorie des jeux,
tradition Gale-Shapley) et de l'autre l'**optimisation combinatoire**
(flots, programmation linéaire, matching bipartite). Chaque algorithme
implémenté puise dans l'une ou l'autre.

---

## 1. Random Serial Dictator (RSD)

### Principe
On tire au sort un ordre sur les élèves, puis chaque élève à son tour
choisit son cours préféré parmi ceux qui ont encore de la place. Trente
lignes de code, aucune bibliothèque externe.

### Motivation
Servir de **référence de simplicité**. Comme le tirage au sort donne à
chaque élève la même chance d'être servi en premier, la procédure est
équitable *en espérance*, transparente et impossible à manipuler : mentir
sur ses préférences ne fait rien gagner.

### Avantages
- **Strategy-proof** au sens fort : la meilleure stratégie est de déclarer
  ses vrais vœux [Abdulkadiroğlu & Sönmez, 1998].
- Complexité linéaire, trivial à implémenter et à auditer.
- Fournit une allocation **Pareto-efficace** en univers déterministe
  (aucun échange à somme positive ne peut être fait ensuite).

### Inconvénients
- Les derniers servis peuvent tout manquer : sur nos données, RSD laisse
  ~10 % de non-affectés là où le flot en laisse 4 %.
- **Injuste ex-post** : la personne servie 340ᵉ paye la position aléatoire.
- Pas d'objectif global — n'exploite pas la structure du problème.

### Références
- [Abdulkadiroğlu, A., & Sönmez, T. (1998). *Random Serial Dictatorship and
  the Core from Random Endowments in House Allocation Problems*.
  Econometrica 66(3), 689-701.](https://doi.org/10.2307/2998583)
- [Bogomolnaia, A., & Moulin, H. (2001). *A New Solution to the Random
  Assignment Problem*. Journal of Economic Theory 100(2), 295-328.](https://doi.org/10.1006/jeth.2000.2710)

---

## 2. Flot de coût minimum (min-cost flow)

### Principe
On modélise chaque bloc comme un réseau : une source d'unités de flot
alimente les élèves ; chaque élève est relié aux occurrences qui lui sont
accessibles, chaque arc portant un coût égal au rang du vœu ; chaque
occurrence est reliée à un puits avec une capacité égale à ses places
disponibles. Le flot de coût minimum qui transporte N unités correspond à
l'affectation optimale pour la somme des rangs.

### Motivation
C'est **le** cadre historique de l'affectation avec capacités [Ford &
Fulkerson, 1962]. Il donne l'**optimum exact** en temps polynomial et se
déguste bien : le graphe se dessine sur un tableau blanc.

### Avantages
- Exact et rapide : moins d'une seconde sur 350 élèves × 9 blocs.
- Prouvable optimal sur la métrique « somme totale des rangs ».
- Bibliothèque `networkx.min_cost_flow` (Python) prête à l'emploi.

### Inconvénients
- Décompose le problème bloc par bloc : ne modélise pas les couplages
  inter-blocs (équité de la somme des rangs par élève, contrainte de
  charge par période).
- Optimise le total, pas l'individu : peut concentrer les mauvais rangs
  sur quelques élèves si cela améliore la moyenne globale.

### Références
- [Ahuja, R. K., Magnanti, T. L., & Orlin, J. B. (1993). *Network Flows :
  Theory, Algorithms, and Applications*. Prentice Hall.](https://www.pearson.com/en-us/subject-catalog/p/network-flows-theory-algorithms-and-applications/P200000005984)
- [Ford, L. R., & Fulkerson, D. R. (1962). *Flows in Networks*. Princeton
  University Press.](https://press.princeton.edu/books/paperback/9780691146676/flows-in-networks)
- Application scolaire : [Duke University Course Assignment](
  https://finance.duke.edu/systems/dukehub/enrollment-registration) et
  la littérature sur l'affectation en école de commerce.

---

## 3. Programmation linéaire en nombres entiers (MIP, CP-SAT)

### Principe
On introduit une variable binaire `x[élève, occurrence]` valant 1 si
l'affectation est faite. On écrit les contraintes en équations
(« au plus un cours par bloc », « capacité ≤ N »), puis on demande au
solveur de trouver la combinaison qui minimise une fonction objectif
(somme des rangs, pire rang, …). Le solveur (Google OR-Tools CP-SAT)
explore un immense arbre de possibilités en coupant les branches non
prometteuses.

### Motivation
Le **cadre le plus flexible**. Toute règle métier — « pas plus de trois
cours dans la même période », « priorité aux redoublants », « équilibrer
FR/EN » — se traduit en une ou deux lignes de contrainte
supplémentaires, sans changer d'algorithme.

### Avantages
- Universel : accepte des objectifs arbitraires (linéaires ou convexes).
- Prouve l'optimalité ou fournit une borne à l'écart.
- Documentation académique et industrielle très abondante.

### Inconvénients
- Passe à l'échelle mais coûte en temps quand la fonction objectif
  devient non séparable (par exemple : pire rang par élève au carré).
- Sensible aux ordres de grandeur : mal calibrer les poids peut
  déstabiliser le solveur.
- Peut ne pas atteindre l'optimum dans un temps raisonnable
  (nous l'avons constaté avec un objectif d'équité min-max).

### Références
- [Wolsey, L. A. (2020). *Integer Programming* (2ᵉ éd.). Wiley.](https://www.wiley.com/en-us/Integer+Programming%2C+2nd+Edition-p-9781119606536)
- [Google OR-Tools CP-SAT documentation](https://developers.google.com/optimization/cp/cp_solver).
- Application universitaire : [Daskalaki, S., Birbas, T., & Housos, E.
  (2004). *An integer programming formulation for a case study in
  university timetabling*. European Journal of Operational Research.](
  https://doi.org/10.1016/S0377-2217(03)00103-6)

---

## 4. Algorithme hongrois (bipartite matching de coût minimum)

### Principe
L'algorithme hongrois [Kuhn, 1955] résout en temps polynomial le problème
d'affectation classique : appariement un-à-un de N travailleurs à N tâches
minimisant le coût total. Pour supporter les capacités > 1, on
**duplique** chaque occurrence autant de fois qu'elle a de places.

### Motivation
Historiquement l'**algorithme de référence** pour tout matching bipartite
pondéré. La bibliothèque SciPy fournit `linear_sum_assignment`, robuste
et bien optimisé.

### Avantages
- Exact, prévisible, très rapide sur matrices de quelques centaines.
- Formulation intuitive : matrice des coûts, sortie une permutation.

### Inconvénients
- Explose en mémoire si les capacités totales atteignent des milliers
  (la matrice devient N × Cap_totale).
- Ne modélise pas naturellement les capacités > 1 ni le couplage
  inter-blocs.

### Références
- [Kuhn, H. W. (1955). *The Hungarian method for the assignment problem*.
  Naval Research Logistics Quarterly 2, 83-97.](https://doi.org/10.1002/nav.3800020109)
- [Munkres, J. (1957). *Algorithms for the Assignment and Transportation
  Problems*. Journal of the SIAM 5(1), 32-38.](https://doi.org/10.1137/0105003)
- [scipy.optimize.linear_sum_assignment](
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html)

---

## 5. Deferred Acceptance (Gale-Shapley)

### Principe
Chaque élève propose son meilleur vœu. Chaque occurrence accepte
provisoirement les meilleurs candidats selon sa capacité (avec une règle
de priorité, ici les anglophones d'abord sur les cours en anglais), et
rejette les autres, qui proposent alors leur choix suivant. Le processus
converge en un nombre fini d'itérations vers un appariement **stable** :
aucune paire (élève, occurrence) ne préférerait mutuellement s'apparier
en dehors du résultat.

### Motivation
C'est le mécanisme utilisé par les grands systèmes d'affectation
scolaire aux États-Unis : Boston Public Schools, New York City High
School Match [Abdulkadiroğlu, Pathak, Roth & Sönmez, 2005]. Sa force
principale est la **robustesse à la déclaration** : côté élèves, dire la
vérité est la stratégie dominante.

### Avantages
- **Strategy-proof côté élèves** [Gale & Shapley, 1962].
- Stabilité garantie : personne ne peut se plaindre qu'un cours accessible
  à un rang meilleur ait accueilli un candidat structurellement moins
  prioritaire.
- Utilisé à grande échelle en production (NRMP pour les médecins
  américains depuis 1952, NYC HS depuis 2003).

### Inconvénients
- **Ne maximise pas le bien-être total** (rang moyen) : préfère la
  stabilité à l'optimum utilitaire.
- Nécessite une notion de priorité côté cours (chez nous : anglophone
  d'abord, puis ordre arbitraire).
- L'implémentation via la bibliothèque `matching` fonctionne bloc par
  bloc — pas de vision cross-blocs.

### Références
- [Gale, D., & Shapley, L. S. (1962). *College Admissions and the
  Stability of Marriage*. American Mathematical Monthly 69(1), 9-15.](
  https://doi.org/10.2307/2312726)
- [Roth, A. E. (1984). *The Evolution of the Labor Market for Medical
  Interns and Residents: A Case Study in Game Theory*. Journal of
  Political Economy 92(6), 991-1016.](https://doi.org/10.1086/261272)
- [Abdulkadiroğlu, A., Pathak, P. A., Roth, A. E., & Sönmez, T. (2005).
  *The Boston Public School Match*. American Economic Review 95(2),
  368-371.](https://doi.org/10.1257/000282805774669637)
- [Prix Nobel d'économie 2012 attribué à Roth et Shapley pour ces
  travaux.](https://www.nobelprize.org/prizes/economic-sciences/2012/summary/)

---

## 6. A-CEEI / Course Match (Approximate Competitive Equilibrium from
Equal Incomes)

### Principe
On simule un marché fictif : chaque élève reçoit un budget presque
identique et « achète » son meilleur panier de cours au prix courant. Un
mécanisme d'ajustement de prix converge vers un équilibre où l'offre
égale la demande. Le résultat possède des garanties d'équité fortes.

### Motivation
Résoudre le problème d'affectation de cours à la **Wharton School**
[Budish, 2011]. Le mécanisme a été déployé sous le nom **Course Match**
pour l'attribution des MBA à Wharton depuis 2013.

### Avantages
- **Envy-free bounded by one course** : aucun élève n'envie durablement
  le panier d'un autre à plus d'un cours près.
- Garanties d'équité formelles (competitive equilibrium).
- Traite naturellement les paniers complets, pas juste les blocs isolés.

### Inconvénients
- **Complexe** à implémenter et à expliquer.
- La bibliothèque `fairpyx` n'expose pas A-CEEI directement — on utilise
  un proxy (`iterated_maximum_matching_adjusted`) qui capture une partie
  de la philosophie d'équité mais pas toutes les propriétés.
- Plus lent que les approches spécialisées ; sensible aux paramètres.

### Références
- [Budish, E. (2011). *The Combinatorial Assignment Problem: Approximate
  Competitive Equilibrium from Equal Incomes*. Journal of Political
  Economy 119(6), 1061-1103.](https://doi.org/10.1086/664613)
- [Budish, E., Cachon, G. P., Kessler, J. B., & Othman, A. (2017).
  *Course Match : A Large-Scale Implementation of Approximate Competitive
  Equilibrium from Equal Incomes for Combinatorial Allocation*.
  Operations Research 65(2), 314-336.](https://doi.org/10.1287/opre.2016.1544)
- [fairpyx — Fair Course Allocation library](
  https://github.com/erelsgl/fairpyx)

---

## 7. Equite (post-traitement du min-cost flow)

### Principe
Approche hybride en deux temps : on part de la solution optimale du min-cost
flow (§2), puis on applique une **recherche locale** :
1. *Déplacements individuels* : chaque élève tente de migrer vers une
   occurrence libre mieux classée dans son bloc.
2. *Swaps par paires* : deux élèves échangent leurs occurrences dans un
   bloc si le maximum de leurs rangs baisse.

Le processus itère jusqu'à ce qu'aucun mouvement n'améliore plus la solution.

### Motivation
Le min-cost flow trouve l'optimum de somme des rangs mais ignore
l'équité inter-blocs (« si un élève a un mauvais rang dans un bloc, cela
peut être compensé par un bon rang dans un autre »). Une recherche locale
est plus simple qu'un MIP global et converge rapidement.

### Avantages
- Domine flow sur **toutes les métriques** dans nos tests
  (1er choix : 67 % vs 58 % ; rang max : 8 vs 10 ; part de rang ≥ 5 :
  0,4 % vs 4,2 %).
- Simple à auditer : chaque swap améliore le max des rangs des deux
  parties concernées, sans dégrader la somme totale.
- Rapide (~ 5 s), déterministe modulo le seed du shuffle.

### Inconvénients
- N'est plus prouvable optimal (recherche locale = optimum local).
- L'heuristique du « max des deux rangs baisse » est efficace mais
  ad-hoc — d'autres critères de swap sont possibles.

### Références
- [Aarts, E., & Lenstra, J. K. (2003). *Local Search in Combinatorial
  Optimization*. Princeton University Press.](
  https://press.princeton.edu/books/paperback/9780691115221/local-search-in-combinatorial-optimization)
- L'idée d'améliorer un flot par swaps est un classique de
  l'optimisation combinatoire, appelée aussi *k-opt* dans le contexte
  du TSP [Lin & Kernighan, 1973].

---

## 8. Upgrade (expérimental, dossier `experiments/`)

### Principe
Variante de Equite avec une **initialisation aléatoire** (chaque élève
prend son meilleur cours libre dans un ordre aléatoire, comme RSD) au
lieu du min-cost flow. Le post-traitement de recherche locale est le
même que Equite.

### Motivation
Voir si partir d'une allocation *hors optimum utilitaire* laisse plus de
marge de manœuvre à la recherche locale pour trouver une meilleure
répartition en termes d'équité.

### Avantages
- Meilleure part de 1er choix : **70 %** (record de nos tests).
- Confirme que l'étape de recherche locale porte l'essentiel du gain.

### Inconvénients
- L'init aléatoire laisse ~200 élèves non affectés (capacités mal
  coordonnées dès le départ) — l'algo ne peut plus les récupérer.
- Non compétitif en production, mais utile comme référence conceptuelle.

---

## 9. Water Filling (expérimental)

### Principe
Chaque élève est initialement placé à son **pire rang accessible** dans
chaque bloc (« au fond du bloc »). Puis à chaque tour, en ordre aléatoire
rotatif, chaque élève tente de **remonter** d'un cran vers un rang
meilleur si l'occurrence cible a de la place. Analogie : chaque bloc est
un tuyau capacitaire ; l'eau (les élèves) monte des niveaux bas
(mauvais rang) vers les hauts (bon rang) tant que le niveau supérieur
n'est pas plein.

### Motivation
Explorer un algorithme totalement différent : maximiser la **compensation**
inter-blocs en donnant a priori à chacun le pire et en promouvant par
équité. Inspiré par les algorithmes de water filling en traitement du
signal [Cover & Thomas, 2006].

### Avantages
- Approche originale, distribution des rangs très étalée.
- Facile à expliquer par la métaphore hydraulique.

### Inconvénients
- Sur nos données : nettement moins bon que Equite (50 % de 1er choix
  vs 67 %, 8 % de rang ≥ 5 vs 0,4 %).
- L'initialisation au pire rang consomme les mauvaises places dès le
  départ, ce qui bloque les promotions ultérieures.
- Utile pour l'expérimentation, pas pour la production.

### Références
- Métaphore water filling : [Cover, T. M., & Thomas, J. A. (2006).
  *Elements of Information Theory* (2ᵉ éd.), section 9.4 sur le water
  filling pour la capacité de canal.](
  https://onlinelibrary.wiley.com/doi/book/10.1002/047174882X)

---

## 10. MIP intégral — CP-SAT avec toutes les contraintes

### Principe
Extension de l'approche MIP §3 : on encode **simultanément** toutes les
règles métier comme contraintes CP-SAT. Le solveur trouve la meilleure
affectation qui respecte tout (exclusion inter-blocs au même créneau,
unicité ECUE, complétude par régime FISE/FISEA distinguée, capacité,
bonus anglophone), avec un terme d'équilibrage des remplissages.

### Motivation
Les autres algorithmes (`flow`, `hungarian`, `mip` simple, `equite`)
résolvent bloc par bloc et laissent silencieusement des collisions
inter-blocs (jusqu'à ~380 élèves avec au moins deux cours au même
moment sur nos données de test). Ce solveur est **le seul qui garantit
la conformité complète** vérifiée par `src/verif_contraintes.py`.

### Avantages
- **Zero violation** des règles de l'enseignante.
- Résout faisabilité + optimalité en un seul appel (branch-and-bound).
- Extensible : nouvelle règle = une ligne de contrainte.

### Inconvénients
- Taux d'affectation légèrement plus faible (~93 % vs 96 %) car refuse
  les solutions non conformes.
- Temps ~7-30 s selon la taille et le time limit.

### Références
- OR-Tools CP-SAT : voir §3.
- L'approche « tout en contraintes » s'appelle *combinatorial
  optimization* ou *constraint programming for scheduling* :
  [Rossi, F., van Beek, P., & Walsh, T. (Éds.) (2006).
  *Handbook of Constraint Programming*. Elsevier.](
  https://www.sciencedirect.com/book/9780444527264/handbook-of-constraint-programming)

---

## 11. Synthèse comparative

| Algo | Optimalité | Contraintes complètes | Équité inter-blocs | Vitesse | Recommandation |
|---|:---:|:---:|:---:|:---:|:---|
| RSD | Pareto-eff. | Non | Faible | ⚡⚡⚡ | Référence |
| Flow / MIP / Hungarian | Optimum somme | Non | Aucune | ⚡⚡ | Comparaison |
| DA | Stabilité | Non | Non | ⚡⚡ | Bien si priorités |
| A-CEEI | Envy-free | Non | Forte | ⚡ | Wharton |
| Equite | Local | Non | Forte | ⚡⚡ | Meilleur rang moyen |
| Upgrade | Local | Non | Forte | ⚡⚡ | Expérimental |
| Water Filling | Aucune | Non | Moyenne | ⚡⚡⚡ | Expérimental |
| **`mip_full`** | **Optimum** | **Oui** | Bonne | ⚡ | **Production** |

---

## Bibliographie complémentaire

Ouvrages de référence pour approfondir :

- [Roth, A. E., & Sotomayor, M. A. O. (1990). *Two-Sided Matching : A
  Study in Game-Theoretic Modeling and Analysis*. Cambridge University
  Press.](https://doi.org/10.1017/CCOL052139015X) — Traité complet sur les
  problèmes d'appariement.
- [Manlove, D. F. (2013). *Algorithmics of Matching Under Preferences*.
  World Scientific.](https://doi.org/10.1142/8591) — Panorama
  algorithmique des variantes de matching.
- [Vazirani, V. V. (2001). *Approximation Algorithms*. Springer.](
  https://link.springer.com/book/10.1007/978-3-662-04565-7) — Cadre général.

Applications réelles récentes :

- [Diebold, F., Aziz, H., Bichler, M., Matthes, F., & Schneider, A.
  (2014). *Course Allocation via Stable Matching*. Business & Information
  Systems Engineering 6(2), 97-110.](https://doi.org/10.1007/s12599-014-0316-6)
- [Bichler, M., Merting, S., & Uzunoglu, A. (2020). *Assigning Course
  Schedules: About Preference Elicitation, Fairness, and Truthfulness*.
  Manufacturing & Service Operations Management.](https://doi.org/10.1287/msom.2020.0879)
- [MIT Course Bidding System — description sur MIT OpenCourseWare](
  https://web.mit.edu/institute-events/course-registration/) et système
  décrit dans [Sönmez, T., & Ünver, M. U. (2010). *Course Bidding at
  Business Schools*. International Economic Review 51(1), 99-123.](
  https://doi.org/10.1111/j.1468-2354.2009.00572.x)

Sur l'éthique et l'équité algorithmique en contexte éducatif :

- [Corbett-Davies, S., & Goel, S. (2018). *The Measure and Mismeasure of
  Fairness: A Critical Review of Fair Machine Learning*. arXiv:1808.00023.](
  https://arxiv.org/abs/1808.00023)
- [Ashlagi, I., & Shi, P. (2016). *Optimal Allocation Without Money: An
  Engineering Approach*. Management Science 62(4), 1078-1097.](
  https://doi.org/10.1287/mnsc.2015.2162)
