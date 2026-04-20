# Projet Fil Rouge Data Engineering avec Python

Ce depot sert de support pedagogique pour un cours complet sur :

- les fondamentaux du Data Engineering
- la construction d'un pipeline de donnees en Python
- l'automatisation de processus metier bases sur des fichiers Excel

L'objectif n'est pas seulement de "faire tourner du code", mais de comprendre comment on passe d'un besoin metier flou a un systeme structure, evolutif et utile pour la prise de decision.

## 1. Scenario du cours

Imagine une entreprise de distribution qui vend plusieurs offres commerciales dans plusieurs magasins. Chaque mois, les equipes terrain exportent leurs ventes dans des fichiers Excel et les deposent dans un dossier partage.

Le probleme est classique :

- les fichiers arrivent au fil de l'eau
- les donnees ne sont pas toujours propres
- les responsables metier veulent des indicateurs fiables
- les decideurs ont besoin d'un rapport lisible, pas de plusieurs CSV techniques

Dans ce projet, l'apprenant joue le role d'un Data Engineer junior qui travaille main dans la main avec des profils metier : direction commerciale, controle de gestion et responsables magasin.

La mission consiste a construire un pipeline simple mais realiste qui :

1. lit les fichiers Excel mensuels
2. garde la memoire de ce qui a deja ete traite
3. nettoie les donnees
4. calcule des KPI utiles
5. produit des sorties metier : un rapport Excel et un dashboard Streamlit

## 2. Les donnees d'entree

Les fichiers sources se trouvent dans `raw_sales_data/`. Ils representent des ventes mensuelles, par exemple `2019-01.xls`, `2019-02.xls`, jusqu'aux mois ajoutes au fur et a mesure du projet.

Chaque fichier contient des transactions commerciales avec des informations du type :

- identifiant de transaction
- magasin
- date de transaction
- offre commerciale
- type de contrat
- montant
- statut eventuel

Ces fichiers representent un cas d'usage tres courant en entreprise : la donnee existe deja, mais elle n'est ni centralisee ni prete pour l'analyse.

### Difficultes realistes introduites par ces fichiers

Ce projet permet de parler de vrais problemes de terrain :

- formats de date heterogenes
- montants non numeriques ou invalides
- identifiants manquants
- doublons
- colonnes parfois incompletes
- executions repetes du pipeline sur le meme historique

Autrement dit, le sujet n'est pas "comment lire un Excel", mais "comment fiabiliser un flux de donnees metier base sur des fichiers".

## 3. Les sorties finales vues par le metier

Le projet produit deux grandes familles de sorties.

### 3.1 Le rapport Excel

Le rapport final est genere dans `outputs/reports/rapport_ventes_latest.xlsx`.

Il contient plusieurs feuilles destinees aux decideurs :

- `Synthese` : vue executive des principaux indicateurs
- `Tendance_Mensuelle` : evolution du chiffre d'affaires dans le temps
- `Performance_Magasins` : classement des magasins
- `Performance_Offres` : performance des offres commerciales
- `Comparaison_Mensuelle` : comparaison du dernier mois disponible avec le mois precedent

Ce rapport ne sert pas a montrer la technique. Il sert a aider un responsable a repondre a des questions concretes :

- combien avons-nous vendu ?
- la tendance est-elle bonne ou mauvaise ?
- quels magasins performent le mieux ?
- quelles offres portent le revenu ?
- qu'est-ce qui a change depuis le mois precedent ?

### 3.2 Le dashboard Streamlit

Le dashboard Streamlit propose une exploration plus interactive des donnees. Il est utile pour :

- filtrer les donnees
- parcourir les KPI
- naviguer plus librement qu'avec un rapport statique

Pedagogiquement, cela permet aussi de montrer qu'un meme socle analytics peut alimenter plusieurs formes de restitution :

- des exports Excel pour les decideurs
- une interface interactive pour l'analyse

## 4. Vue d'ensemble du pipeline

Il est important de distinguer deux vues.

### 4.1 Vue fonctionnelle

Du point de vue du metier, le pipeline fait ceci :

1. il recupere les nouveaux fichiers de ventes
2. il verifie ce qui a deja ete charge
3. il nettoie les nouvelles lignes utiles
4. il met a jour les indicateurs
5. il regenere les sorties de reporting si le contenu a evolue

Cette logique est au coeur du projet : on ne refait pas tout a chaque fois, on traite intelligemment ce qui a change.

### 4.2 Vue technique

Du point de vue du code, le projet est structure par responsabilites :

- `src/ingestion/` : lecture et normalisation des fichiers Excel
- `src/transformation/` : nettoyage et standardisation des transactions
- `src/analytic/` : calcul et mise a jour incremental des KPI
- `src/reporting/` : production des sorties metier
- `src/pipeline.py` : orchestration de bout en bout
- `run_pipeline.py` : point d'entree minimal

Cette separation est fondamentale. Elle permet de comprendre qu'un pipeline propre n'est pas un gros script unique, mais un ensemble de modules specialises.

## 5. Les etapes du pipeline en detail

### 5.1 Ingestion

L'ingestion consiste a decouvrir les fichiers Excel disponibles, lire leur contenu et normaliser les colonnes attendues.

Concept introduit :

- file-based ingestion

Pourquoi c'est important :

- dans beaucoup d'organisations, les donnees arrivent d'abord sous forme de fichiers
- avant de parler base de donnees, cloud ou streaming, il faut savoir fiabiliser ce type d'entree

### 5.2 Ingestion incrementale

Le pipeline ne relit pas tout `raw_sales_data/` a chaque execution. Il s'appuie sur `outputs/ingestion/ingestion_metadata.csv` pour savoir quels fichiers ont deja ete charges.

Concept introduit :

- etat du pipeline
- traitement incremental

Pourquoi c'est important :

- on evite le retraitement inutile
- on gagne en temps d'execution
- on se rapproche d'un vrai systeme de production

### 5.3 Transformation

La transformation nettoie les transactions :

- suppression des lignes invalides
- normalisation des types
- filtrage par statut
- deduplication

Concept introduit :

- data cleaning
- quality gates

Pourquoi c'est important :

- les KPI n'ont de valeur que si la donnee source est fiable
- en pratique, la qualite des donnees est un sujet central du metier

### 5.4 Transformation incrementale

La transformation ne repart pas de zero inutilement. Elle identifie les fichiers deja presents dans la sortie nettoyee et ne traite que les elements manquants.

Concept introduit :

- incremental processing sur une etape de nettoyage

Pourquoi c'est plus subtil que l'ingestion :

- il ne suffit pas de detecter un nouveau fichier
- il faut aussi garder la coherence de la sortie nettoyee

### 5.5 Calcul des KPI

L'etape analytics produit des tables metier :

- vue de synthese
- KPI mensuels
- KPI par magasin
- KPI par offre
- rapports de qualite et inventaire analytics

Concept introduit :

- agregation
- indicateurs de pilotage
- mesures derivees

Exemples de KPI :

- chiffre d'affaires total
- nombre de transactions
- panier moyen
- part de nouveaux contrats
- croissance mensuelle

### 5.6 Reporting Excel et Streamlit

Le reporting transforme les sorties techniques en sorties de decision.

Pour l'Excel :

- un seul fichier de reference est conserve : `rapport_ventes_latest.xlsx`
- le rapport n'est regenere que si son contenu a change
- une comparaison du dernier mois avec le precedent est integree

Pour Streamlit :

- on dispose d'une lecture plus exploratoire des KPI

Concept introduit :

- reporting oriente utilisateur
- difference entre couche technique et couche de presentation

## 6. Parcours d'apprentissage par branches

Le projet a ete construit comme une progression pedagogique. Chaque branche correspond a une etape de maturite.

### `main`

Point de depart minimal.

Ce que l'on apprend :

- structurer un petit projet Python
- definir un point d'entree

### `learn/incremental_ingestion`

Probleme traite :

- eviter de recharger les memes fichiers a chaque run

Concept introduit :

- memoire du pipeline

Decision de conception :

- utiliser un fichier CSV de metadonnees plutot qu'une base externe pour rester simple et pedagogique

### `transformation/cleaning`

Probleme traite :

- les donnees brutes ne sont pas exploitables telles quelles

Concept introduit :

- nettoyage des donnees
- verification des colonnes obligatoires

### `transformation_incrementale`

Probleme traite :

- ne pas nettoyer tout l'historique a chaque execution

Concept introduit :

- incremental sur une vue transformee

### `analytic/kpis.py`

Probleme traite :

- transformer des transactions nettoyees en indicateurs de pilotage

Concept introduit :

- KPI
- agregats
- mesures derivees

### `reporting/streamlit_app`

Probleme traite :

- permettre une lecture interactive des resultats

Concept introduit :

- data app simple
- restitution visuelle

### `improve_streamlit`

Probleme traite :

- rendre le dashboard plus lisible et plus utile

Concept introduit :

- ergonomie
- presentation de KPI

### `reporting/excel`

Probleme traite :

- fournir une sortie metier facilement partageable

Concept introduit :

- reporting Excel automatise avec `xlsxwriter`

### `reporting/improve_excel_report`

Probleme traite :

- ne garder qu'un rapport de reference
- eviter les doublons
- mieux expliquer les evolutions d'un mois a l'autre

Concept introduit :

- gestion du cycle de vie des rapports
- fingerprint de contenu
- comparaison mensuelle

## 7. Concepts cles expliques pour debutants

### Qu'est-ce qu'un pipeline de donnees ?

Une bonne analogie est celle d'une chaine de production.

- la matiere premiere = les fichiers Excel bruts
- l'atelier de nettoyage = la transformation
- le controle qualite = les verifications metier
- le tableau de bord = le reporting

Un pipeline sert donc a faire circuler, transformer et fiabiliser une donnee jusqu'a un usage utile.

### Qu'est-ce que l'incremental ?

L'incremental consiste a traiter seulement ce qui est nouveau ou manquant, plutot que de tout recalculer.

Pourquoi c'est une bonne idee :

- plus rapide
- plus economique
- plus proche des pratiques reelles

### Pourquoi separer les modules ?

Parce que chaque etape repond a une question differente :

- l'ingestion lit
- la transformation nettoie
- l'analytics calcule
- le reporting presente
- le pipeline orchestre

Cette separation rend le projet plus lisible, plus testable et plus evolutif.

### Pourquoi `Path`, les packages et les `__init__.py` comptent-ils ?

Ce projet est aussi un support pour apprendre a structurer proprement un projet Python :

- `pathlib.Path` rend les chemins plus robustes
- la structure `src/...` clarifie les responsabilites
- les packages rendent les imports plus coherents

## 8. Contenu reutilise depuis `apprendre_python.md`

Le fichier [apprendre_python.md](/home/vant/Documents/automate-excel-with-python/apprendre_python.md) contient le detail pedagogique de la progression. Le `README.md` en reutilise les idees les plus utiles :

- le role de `run_pipeline.py` comme point d'entree minimal
- l'importance de `Path` pour manipuler les chemins
- la logique du traitement incremental
- la separation entre orchestration et logique metier
- le lien entre qualite des donnees et fiabilite des KPI
- la difference entre sorties techniques et sorties metier

Le README reorganise ces explications pour servir de document de cours principal, plus lisible pour un debutant.

## 9. Choix de conception et bonnes pratiques

### Pourquoi ce projet est simple, mais sain

Le projet fait volontairement des choix simples :

- pas de base de donnees
- pas d'orchestrateur externe
- pas de conteneurisation
- pas de cloud

Ces limites sont pedagogiques, pas accidentelles.

Elles permettent de concentrer l'apprentissage sur les fondements :

- structurer un pipeline
- raisonner en etapes
- introduire l'incremental
- produire de la valeur metier

### Les compromis assumes

Ce projet privilegie :

- la clarte plutot que la sophistication
- la lecture du code plutot que l'abstraction excessive
- les fichiers comme support d'etat plutot qu'une infrastructure plus lourde

En contrepartie, ce systeme serait limite a plus grande echelle :

- concurrence faible
- pas de gestion multi-utilisateurs
- pas de stockage transactionnel
- pas de monitoring industriel

### Comment le projet pourrait evoluer vers la production

Voici des prolongements naturels pour des apprenants plus avances :

- remplacer l'etat fichier par une base de donnees
- orchestrer avec Airflow, Prefect ou Dagster
- stocker les donnees dans un data warehouse
- exposer les KPI via une API
- ajouter des tests automatises
- deployer le dashboard
- historiser les rapports dans un stockage objet

## 10. Comment executer le projet

### Lancer le pipeline

Depuis la racine du projet :

```bash
python3 run_pipeline.py
```

Cette commande :

- lit les nouveaux fichiers de `raw_sales_data/`
- met a jour les sorties dans `outputs/`
- produit ou reutilise le rapport Excel metier

### Lancer le dashboard Streamlit

```bash
streamlit run src/reporting/streamlit_app.py
```

### Comprendre les sorties

Tu trouveras notamment :

- `outputs/ingestion/` : donnees chargees et metadonnees d'ingestion
- `outputs/transformation/` : donnees nettoyees
- `outputs/analytics/` : tables KPI
- `outputs/reports/rapport_ventes_latest.xlsx` : rapport metier de reference
- `outputs/logs/pipeline.log` : traces d'execution

## 11. Ce que l'apprenant maitrise a la fin

A la fin de ce projet, un debutant doit etre capable de :

- expliquer ce qu'est un pipeline de donnees
- structurer un projet Python par modules
- raisonner en ingestion, transformation, analytics et reporting
- comprendre pourquoi l'incremental est important
- produire des KPI a partir de donnees brutes
- relier une architecture technique a un besoin metier

## 12. Conclusion et suites possibles

Ce projet est volontairement accessible, mais il couvre deja une grande partie des questions fondatrices du Data Engineering :

- comment faire entrer des donnees dans un systeme
- comment nettoyer ces donnees
- comment eviter les recalculs inutiles
- comment transformer la technique en valeur metier

En ce sens, ce depot peut servir de projet de reference pour introduire :

- les pipelines de donnees
- l'automatisation Python
- la qualite des donnees
- le reporting decisionnel

### Prochaines extensions pedagogiques

Pour prolonger le cours, tu pourrais ajouter :

- une couche base de donnees
- une orchestration planifiee
- des tests unitaires et d'integration
- du versioning de donnees
- des visualisations plus riches
- un deploiement cloud

Le message central du cours est le suivant :

un bon projet data ne commence pas par la complexite technique. Il commence par une bonne comprehension du besoin, une structure claire, et des choix de conception coherents.
