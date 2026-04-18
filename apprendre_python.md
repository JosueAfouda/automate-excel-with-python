# Apprendre Python avec ton pipeline Excel

## 1. Ce que fait maintenant ton projet

Ton projet contient maintenant une premiere version de pipeline :

- `run_pipeline.py` lance l'execution
- `src/pipeline.py` orchestre les etapes
- `src/ingestion/sales_ingestion.py` charge les fichiers Excel
- les resultats sont ecrits dans `outputs/ingestion/`

Pour l'instant, une seule etape est active : l'ingestion.

Les deux fichiers CSV generes sont :

- `business_data.csv` : les donnees metier chargees depuis les fichiers Excel
- `ingestion_metadata.csv` : les metadonnees de chargement de chaque fichier

## 2. Les erreurs et points a corriger dans ton code initial

### Dans `run_pipeline.py`

Tu avais ecrit :

```python
outputs = run_pipeline
```

Ici, tu stockais la fonction elle-meme, mais tu ne l'executais pas.

En Python :

- `run_pipeline` = la fonction
- `run_pipeline()` = l'appel de la fonction

La correction etait donc de faire :

```python
outputs = run_pipeline()
```

### Dans `src/pipeline.py`

Le fichier etait incomplet :

```python
def run_pipeline() -> dict[str, Path]:
    ingestion_result =
```

Il manquait :

- l'appel a la fonction `load_sales_data()`
- la sauvegarde des resultats en CSV
- la creation du dossier de sortie
- la valeur de retour

### Dans la structure du projet

Ton projet utilisait deja `src/...`, ce qui est bien, mais il manquait des fichiers `__init__.py`.

Ces fichiers servent a rendre la structure plus explicite comme package Python :

- `src/__init__.py`
- `src/ingestion/__init__.py`
- `src/transformation/__init__.py`

Aujourd'hui, Python peut parfois fonctionner sans eux grace aux namespace packages, mais pour apprendre et pour garder un projet clair, les ajouter est une bonne pratique.

### Dans `sales_ingestion.py`

Le code etait globalement bon. J'ai surtout apporte des corrections de proprete et de maintenabilite :

- factorisation du chemin racine du projet
- ajout de docstrings courtes
- ajout d'un parametre optionnel `source_dir`
- correction d'un message d'erreur : `valide` -> `valid`

## 3. Les concepts Python importants a comprendre

## 3.1 Les imports entre modules

Dans ton projet, `run_pipeline.py` importe :

```python
from src.pipeline import run_pipeline
```

Cela veut dire :

- va dans le package `src`
- ouvre le module `pipeline.py`
- importe la fonction `run_pipeline`

Dans `src/pipeline.py`, j'ai utilise un import relatif :

```python
from .ingestion.sales_ingestion import IngestionResult, load_sales_data
```

Le point `.` veut dire : "depuis le package courant (`src`), va dans `ingestion`".

Pourquoi c'est utile ?

- le code reste coherent a l'interieur du package
- on voit clairement que `pipeline.py` depend d'un sous-module du meme projet

## 3.2 Les chemins avec `pathlib`

`pathlib.Path` est la maniere moderne de manipuler les chemins en Python.

Exemple :

```python
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
output_dir = project_root / "outputs" / "ingestion"
```

Points importants :

- `__file__` = chemin du fichier Python courant
- `.resolve()` = transforme ce chemin en chemin absolu
- `.parents[1]` = remonte d'un niveau dans l'arborescence
- l'operateur `/` permet de construire un chemin proprement

Pourquoi ne pas ecrire une chaine comme `"outputs/ingestion"` partout ?

- c'est plus fragile
- cela depend du dossier depuis lequel tu lances Python
- `Path` rend le code plus lisible et plus robuste

## 3.3 Les type hints

Exemple :

```python
def run_pipeline(output_dir: Path | None = None) -> dict[str, Path]:
```

Cela signifie :

- `output_dir` peut etre un objet `Path`
- ou `None`
- la fonction renvoie un dictionnaire dont :
  - les cles sont des `str`
  - les valeurs sont des `Path`

Les type hints ne bloquent pas Python a l'execution, mais ils aident beaucoup pour :

- comprendre le code
- utiliser l'autocompletion
- detecter certaines erreurs plus tot

## 3.4 Les fonctions et les parentheses

C'est une erreur tres classique :

```python
result = my_function
```

ne fait pas la meme chose que :

```python
result = my_function()
```

La premiere ligne stocke la fonction.
La seconde ligne execute la fonction.

## 3.5 Les packages et `__init__.py`

Quand un dossier Python contient un `__init__.py`, on le traite classiquement comme un package.

Exemple :

- `src/`
- `src/ingestion/`
- `src/transformation/`

Cela facilite :

- les imports
- l'organisation du code
- l'evolution du projet quand il grossit

## 4. Les corrections que j'ai faites

## 4.1 Dans `src/pipeline.py`

J'ai ajoute trois fonctions :

### `get_project_root()`

Elle calcule la racine du projet a partir du fichier courant.

Interet :

- eviter les chemins ecrits en dur
- centraliser la logique de chemin

### `save_ingestion_outputs(...)`

Cette fonction :

- cree le dossier de sortie si necessaire
- sauvegarde les deux DataFrames en CSV
- retourne les chemins generes

Interet :

- separer l'orchestration du pipeline et la logique d'ecriture
- faciliter l'ajout d'autres etapes plus tard

### `run_pipeline(...)`

Cette fonction :

- choisit le dossier de sortie
- appelle `load_sales_data()`
- delegue la sauvegarde a `save_ingestion_outputs(...)`

Interet :

- garder un point central pour enchainer les futures etapes

Plus tard, tu pourras faire quelque chose comme :

```python
def run_pipeline(output_dir: Path | None = None) -> dict[str, Path]:
    ingestion_result = load_sales_data()
    cleaned_data = clean_sales_data(ingestion_result.data)
    kpis = compute_kpis(cleaned_data)
```

## 4.2 Dans `run_pipeline.py`

J'ai corrige l'appel de la fonction et j'ai ajoute un affichage simple :

```python
outputs = run_pipeline()
```

Puis :

```python
for output_name, output_path in outputs.items():
    print(f"- {output_name}: {output_path}")
```

Cela te permet de voir directement quels fichiers ont ete produits.

## 4.3 Dans `sales_ingestion.py`

J'ai garde ton approche generale car elle etait saine :

- decouverte des fichiers Excel
- normalisation des colonnes
- concat des donnees
- creation d'un inventaire d'ingestion

Les ameliorations ajoutees :

- `get_project_root()` pour eviter de repeter la logique de chemin
- `source_dir: Path | None = None` pour rendre le code plus flexible
- docstrings pour expliquer rapidement le role des fonctions
- petits nettoyages de style et de messages d'erreur

## 5. Pourquoi cette structure est evolutive

Ton fichier `src/pipeline.py` joue maintenant le bon role : il orchestre.

Cela veut dire :

- les fonctions metier restent dans leurs modules specialises
- le pipeline les appelle dans le bon ordre
- les sorties sont centralisees

Quand tu ajouteras la transformation, tu pourras :

1. creer un module dedie
2. importer sa fonction dans `src/pipeline.py`
3. enchainer l'etape apres l'ingestion

Cette separation est importante :

- `ingestion` = lire les donnees
- `transformation` = nettoyer / enrichir
- `kpi` = calculer les indicateurs
- `pipeline` = coordonner l'ensemble

## 6. Ce que tu dois retenir en priorite

Si tu ne retiens que l'essentiel, retiens ceci :

1. Une fonction s'execute avec des parentheses : `fonction()`.
2. `Path` est preferable aux chemins ecrits a la main dans des chaines.
3. Le pipeline doit orchestrer les etapes, pas contenir toute la logique metier.
4. Les type hints aident a comprendre le code, meme si Python ne les impose pas.
5. Une bonne structure de projet devient tres importante des que tu ajoutes plusieurs etapes.

## 7. Commande pour lancer ton pipeline

Depuis la racine du projet :

```bash
python3 run_pipeline.py
```

Tu devrais obtenir des fichiers dans :

```text
outputs/ingestion/
```

## 8. Prochaine etape recommandee

La prochaine bonne etape pedagogique serait d'ajouter une etape de transformation simple dans `src/transformation/cleaning.py`, puis de la brancher dans `src/pipeline.py`.

De cette maniere, tu pratiqueras concretement :

- les imports entre modules
- le passage de DataFrame d'une etape a l'autre
- l'organisation propre d'un projet Python

## 9. Comprendre le traitement incremental

### Idee generale

Ce que tu cherches s'appelle du traitement incremental.

Au lieu de relire tout `raw_sales_data/` a chaque execution, le pipeline doit repondre a une question simple avant d'ingerer un fichier :

> "Est-ce que ce fichier a deja ete traite ?"

Si la reponse est oui, on le saute. Si la reponse est non, on le traite, puis on garde une trace de ce traitement.

### La strategie a utiliser

La bonne strategie consiste a ajouter une memoire du pipeline.

Aujourd'hui, ton pipeline lit les fichiers presents. Demain, il doit lire :

1. la liste des fichiers disponibles dans `raw_sales_data/`
2. la liste des fichiers deja ingeres
3. la difference entre les deux

Ensuite :

1. il ne traite que les fichiers "nouveaux"
2. il met a jour son historique de traitement
3. il produit ses sorties habituelles

Conceptuellement, ton pipeline passe donc de :

- "je traite tous les fichiers trouves"

a :

- "je traite seulement les fichiers non encore enregistres comme ingeres"

C'est la base de beaucoup de pipelines reels.

### Les approches possibles

#### Approche A : suivi par nom de fichier

On enregistre quelque part les noms deja traites, par exemple :

- `2019-01.xls`
- `2019-02.xls`
- `2019-03.xls`

Au prochain run, si `2019-04.xls` apparait et n'est pas dans l'historique, on le traite.

Avantages :

- tres simple a comprendre
- tres simple a implementer
- suffisant si les fichiers sont immuables
- tres adapte a ton cas actuel

Inconvenients :

- si un fichier existant est modifie mais garde le meme nom, le pipeline ne le verra pas
- suppose que le nom du fichier est fiable comme identifiant metier

#### Approche B : suivi par nom + date de modification

On stocke pour chaque fichier :

- son nom
- sa date de derniere modification

Si le nom est connu mais que la date a change, on peut decider de le retraiter.

Avantages :

- plus robuste que le seul nom
- detecte certains fichiers modifies

Inconvenients :

- la date de modification peut changer pour des raisons non metier
- moins stable si les fichiers sont copies ou deplaces
- un peu plus subtil a expliquer et tester

#### Approche C : suivi par hash du fichier

On calcule une empreinte du contenu, par exemple un hash.
Si le hash est nouveau, on traite. Si le hash est deja connu, on saute.

Avantages :

- tres fiable pour detecter un vrai changement de contenu
- utile en production quand les fichiers peuvent etre modifies

Inconvenients :

- plus couteux a calculer
- plus complexe conceptuellement
- probablement excessif pour ton projet actuel

#### Approche D : suivi via une table de metadonnees d'ingestion

Le pipeline garde un "journal d'ingestion" avec des colonnes du type :

- `source_file`
- `ingested_at`
- `status`
- `rows_loaded`
- eventuellement `file_size`, `mtime`, `hash`

C'est en fait une version structuree des approches precedentes.

Avantages :

- tres proche des pratiques reelles en data engineering
- tracabilite claire
- extensible dans le temps

Inconvenients :

- demande de penser a la persistance de cet etat
- un peu plus de design au depart

#### Approche E : decoupage par periode metier

Comme tes fichiers sont mensuels (`2019-01`, `2019-02`, etc.), on pourrait raisonner par mois deja charges.

Avantages :

- simple si chaque fichier correspond exactement a une periode unique
- logique metier claire

Inconvenients :

- fragile si un mois est corrige plus tard
- trop dependant de la convention de nommage
- moins generique que le suivi de fichier

### La solution la plus simple et la plus adaptee pour ton projet

Pour ton projet actuel, la meilleure solution est :

- un journal de fichiers deja ingeres
- base au minimum sur le nom de fichier
- stocke dans un fichier de metadonnees persistant

Pourquoi c'est le meilleur choix maintenant :

- ton pipeline travaille sur des fichiers mensuels bien nommes
- ton besoin principal est de ne pas retraiter les anciens fichiers
- tu es encore en phase d'apprentissage
- il faut une solution claire avant une solution "parfaite"

Autrement dit : commence simple et propre.

La version la plus raisonnable pour toi est :

- enregistrer les fichiers traites avec leur statut
- au prochain run, ignorer ceux deja marques comme `loaded`

Si plus tard tu veux gerer les fichiers modifies, tu pourras enrichir ce suivi avec :

- taille
- date de modification
- hash

### Integration conceptuelle dans ton pipeline actuel

Ton pipeline peut etre pense en 4 blocs logiques :

1. Decouverte
   lire les fichiers presents dans `raw_sales_data/`
2. Lecture de l'etat
   lire l'historique des fichiers deja ingeres
3. Filtrage
   identifier les fichiers nouveaux a traiter et ceux a ignorer
4. Ingestion + mise a jour de l'etat
   traiter uniquement les nouveaux fichiers puis enregistrer qu'ils ont ete traites

Conceptuellement, `src/pipeline.py` devrait orchestrer cela, et `sales_ingestion.py` devrait rester centre sur l'ingestion elle-meme.

Donc la separation des responsabilites serait :

- `sales_ingestion.py` : comment lire et normaliser un fichier Excel
- `pipeline.py` : quels fichiers faut-il traiter cette fois
- `run_pipeline.py` : lancer l'ensemble

C'est une tres bonne architecture pour la suite.

### Ce que cela t'apprend sur les pipelines reels

Dans un vrai pipeline, on evite le retraitement total pour trois raisons :

- performance
- cout
- fiabilite operationnelle

Le principe cle est toujours le meme :

- les donnees brutes arrivent
- le pipeline garde un etat
- cet etat permet de decider ce qui est nouveau

C'est cela, le coeur de l'incremental.

En pratique, les pipelines reels utilisent souvent :

- un fichier de suivi
- une table de base de donnees
- une table de logs d'ingestion
- parfois un systeme de versionnement ou de hash

### Recommandation finale

Pour ton projet actuel, je te conseille de viser ce design :

- un fichier d'etat d'ingestion persistant
- une entree par fichier traite
- au depart, suivi par nom de fichier + statut
- plus tard, si besoin, ajout de `mtime` ou de `hash`

C'est le meilleur compromis entre :

- simplicite
- pedagogie
- robustesse
- evolutivite

## 10. Passage a l'implementation incrementale

Cette section explique les modifications techniques qui ont ete faites dans le projet pour passer d'une ingestion complete a une ingestion incrementale.

### Le principe retenu

J'ai reutilise le fichier deja produit par ton pipeline :

- `outputs/ingestion/ingestion_metadata.csv`

Ce fichier joue maintenant le role de memoire du pipeline.

L'idee est la suivante :

1. le pipeline liste les fichiers presents dans `raw_sales_data/`
2. il lit `ingestion_metadata.csv`
3. il recupere les fichiers deja ingeres avec succes
4. il ne traite que les fichiers absents de cet historique
5. il ajoute ensuite les nouvelles donnees aux sorties existantes

Autrement dit, l'etat du pipeline n'est plus seulement dans le code, il est aussi dans les fichiers de sortie.

### Pourquoi cette approche colle bien a ton projet

Cette solution est adaptee a ton codebase actuel parce que :

- tu avais deja un fichier de metadonnees d'ingestion
- ce fichier contient deja `source_file`
- ton pipeline travaille sur des fichiers mensuels bien identifies
- tu n'as pas besoin pour l'instant d'une base de donnees ou d'un systeme plus complexe

J'ai toutefois choisi d'utiliser en interne la paire :

- `source_folder`
- `source_file`

au lieu de `source_file` seul.

Pourquoi ?

- cela evite de confondre deux fichiers de meme nom venant de dossiers differents
- c'est plus robuste sans rendre le code beaucoup plus complexe

### Ce qui a change dans `src/pipeline.py`

Le role de `src/pipeline.py` a ete renforce : il orchestre maintenant le traitement incremental.

#### 1. Lecture de l'etat existant

Une fonction lit `ingestion_metadata.csv` si le fichier existe deja.

Si le fichier n'existe pas, le pipeline considere qu'il s'agit d'un premier lancement.

Cela permet de distinguer :

- premier run : tout est nouveau
- runs suivants : seuls les nouveaux fichiers sont traites

#### 2. Identification des fichiers deja charges

Le pipeline recupere les fichiers dont le `status` est `loaded`.

Ce point est important :

- seuls les fichiers charges avec succes sont consideres comme deja traites
- un fichier en erreur n'est pas considere comme valide pour le skip

Conceptuellement, cela revient a dire :

- `loaded` = on peut ignorer ce fichier au prochain run
- `error` = on ne doit pas le considerer comme termine

#### 3. Filtrage des nouveaux fichiers

Le pipeline compare :

- les fichiers presents dans `raw_sales_data/`
- les fichiers deja enregistres dans le journal d'ingestion

La difference entre les deux correspond a la liste des nouveaux fichiers a ingerer.

#### 4. Fusion avec les sorties existantes

Quand de nouveaux fichiers sont charges, le pipeline :

- lit `business_data.csv` s'il existe
- ajoute les nouvelles lignes aux anciennes
- lit `ingestion_metadata.csv` s'il existe
- ajoute les nouvelles metadonnees

Ensuite, il reecrit les deux CSV.

Ce point est crucial :

- si tu ne faisais que sauvegarder les donnees du dernier run, tu perdrais l'historique precedent
- ici, on conserve les anciennes donnees et on append les nouvelles

#### 5. Verification de coherence des sorties

J'ai ajoute une verification de securite :

- soit `business_data.csv` et `ingestion_metadata.csv` existent tous les deux
- soit aucun des deux n'existe encore

Pourquoi ?

Parce que si un seul des deux est present, l'etat incremental devient ambigu.

Exemple :

- si les metadonnees existent mais pas `business_data.csv`, le pipeline pourrait croire que tout a deja ete traite alors que les donnees finales sont absentes

Dans ce cas, le code leve une erreur claire au lieu de continuer dans un etat incoherent.

### Ce qui a change dans `src/ingestion/sales_ingestion.py`

Le module d'ingestion garde son role principal : savoir lire et normaliser des fichiers Excel.

Mais je l'ai legerement refactorise pour le rendre compatible avec le filtrage fait par le pipeline.

#### 1. Nouvelle fonction `load_sales_files(...)`

Avant, l'ingestion faisait directement :

- decouverte des fichiers
- lecture de tous les fichiers trouves

Maintenant, il y a une fonction dediee qui charge explicitement une liste de fichiers deja selectionnes.

Pourquoi c'est mieux ?

- `pipeline.py` choisit quels fichiers traiter
- `sales_ingestion.py` se contente de les lire

Cette separation des responsabilites est importante.

#### 2. `load_sales_data(...)` devient un wrapper

La fonction `load_sales_data(...)` existe toujours, mais elle sert maintenant surtout de raccourci :

1. elle decouvre tous les fichiers
2. elle appelle ensuite la fonction qui charge la liste fournie

Cela garde ton API initiale simple, tout en rendant le module plus flexible.

#### 3. Gestion d'un resultat vide cote donnees

J'ai ajoute une structure vide pour les donnees d'ingestion.

Pourquoi ?

Si un lot de nouveaux fichiers ne produit aucune ligne valide, on veut quand meme garder une structure de DataFrame previsible.

Cela rend le code plus robuste pour les cas limites.

### Le comportement du pipeline apres modification

#### Cas 1 : premier lancement

Si aucun fichier de sortie n'existe encore :

- le pipeline traite tous les fichiers de `raw_sales_data/`
- il cree `business_data.csv`
- il cree `ingestion_metadata.csv`

#### Cas 2 : nouveau fichier ajoute

Exemple :

- `2019-01.xls`, `2019-02.xls`, `2019-03.xls` sont deja enregistres
- tu ajoutes `2019-04.xls`

Au run suivant :

- les trois anciens fichiers sont ignores
- seul `2019-04.xls` est charge
- ses lignes sont ajoutees a `business_data.csv`
- ses metadonnees sont ajoutees a `ingestion_metadata.csv`

#### Cas 3 : aucun nouveau fichier

Si tous les fichiers presents sont deja connus avec le statut `loaded` :

- aucun fichier Excel n'est relu
- les CSV de sortie sont laisses tels quels

Cela evite le retraitement inutile.

### Ce que cette implementation t'apprend

Cette evolution du projet illustre tres bien une idee cle du data engineering :

- un pipeline ne fait pas seulement des calculs
- il maintient aussi un etat

Dans ton projet, cet etat est actuellement un simple fichier CSV de metadonnees.

Dans des systemes plus avances, le meme principe existe, mais l'etat peut etre stocke dans :

- une base SQL
- une table de logs d'ingestion
- un catalogue de donnees
- un orchestrateur de pipeline

Le concept reste pourtant le meme :

- observer ce qui a deja ete fait
- ne traiter que ce qui est nouveau

### Pourquoi cette architecture est saine pour la suite

Tu peux maintenant faire evoluer ton projet dans une bonne direction :

- ajouter une etape de transformation incrementalement
- calculer plus tard des KPI sans recharger tout l'historique
- enrichir le suivi avec `mtime`, `file_size` ou `hash` si besoin

L'avantage est que tu n'as pas change brutalement ton architecture.

Tu as simplement rendu :

- `pipeline.py` plus intelligent dans ses decisions
- `sales_ingestion.py` plus modulaire

C'est exactement le type de refactorisation progressive qu'on recherche dans un vrai projet Python.

## 11. Garder `run_pipeline.py` simple et utiliser des logs

J'ai finalement corrige un point d'architecture important :

- `run_pipeline.py` doit rester aussi simple que possible
- les messages operationnels ne doivent pas etre portes par des `print()`

### Pourquoi `run_pipeline.py` doit rester minimal

Le fichier `run_pipeline.py` est un point d'entree.

Son role ideal est simplement :

1. importer le pipeline
2. appeler le pipeline

Pourquoi ce choix est bon ?

- le fichier reste stable au fil du projet
- il ne melange pas logique metier et logique d'execution
- il est plus facile a reutiliser plus tard avec un orchestrateur, un cron, Airflow ou un job batch

Dans ton projet, cela veut dire qu'on prefere quelque chose de tres simple :

```python
from src.pipeline import run_pipeline

def main() -> None:
    run_pipeline()
```

### Pourquoi `print()` n'est pas une bonne strategie

Les `print()` peuvent depanner au debut, mais ce n'est pas une bonne solution de production.

Le probleme principal est que `print()` :

- n'a pas de niveau (`INFO`, `WARNING`, `ERROR`)
- n'est pas structure
- est plus difficile a filtrer
- est moins pratique a rediriger vers des fichiers ou des systemes de supervision

En production, on prefere des logs.

### Ce que j'ai mis en place a la place

J'ai laisse `run_pipeline.py` minimal, et j'ai ajoute du logging dans :

- `src/pipeline.py`
- `src/ingestion/sales_ingestion.py`

L'idee est que ce soient les modules metier qui racontent :

- ce qu'ils sont en train de faire
- combien de fichiers ils ont detectes
- combien de fichiers sont nouveaux
- combien sont ignores
- combien de lignes ont ete chargees
- quelles erreurs sont survenues

### Exemples d'informations maintenant portees par les logs

Le pipeline journalise des evenements comme :

- debut d'execution du pipeline
- chargement du fichier `ingestion_metadata.csv`
- nombre de fichiers detectes
- nombre de fichiers nouveaux et ignores
- absence de nouveaux fichiers
- ecriture des CSV de sortie

Le module d'ingestion journalise aussi :

- lecture de chaque fichier Excel
- nombre de lignes chargees par fichier
- erreur detaillee si un fichier ne peut pas etre lu

### Pourquoi cette approche est meilleure

Cette approche est plus saine parce que :

- `run_pipeline.py` reste stable et neutre
- les messages vivent pres de la logique qui les produit
- le pipeline est plus facile a observer et deboguer
- le projet se rapproche d'une vraie pratique de production

### Point important sur la configuration des logs

Ajouter des appels a `logger.info(...)` ne veut pas dire qu'il faut configurer les logs dans `run_pipeline.py`.

En general, la configuration des logs se fait a un niveau superieur :

- dans un script d'execution dedie
- dans un orchestrateur
- dans un service
- dans l'environnement de production

Cela permet de separer :

- la production des logs
- la configuration des logs

Cette separation est une bonne pratique.

## 12. Pourquoi aucun fichier de log n'etait cree

Tu as rencontre un comportement tres classique en Python :

- le code appelait bien `logger.info(...)`
- mais aucun fichier de log n'etait cree

Cela arrive quand on confond deux choses differentes :

1. produire un message de log
2. configurer la destination de ce message

### Produire un log ne suffit pas

Quand tu ecris :

```python
logger.info("Starting pipeline run")
```

tu demandes simplement a Python de creer un evenement de log.

Mais cela ne dit pas encore :

- ou l'ecrire
- dans quel format
- dans un fichier ou dans la console
- avec quel niveau minimal

Sans configuration, ces messages peuvent etre ignores ou ne jamais etre ecrits dans un fichier.

### La correction apportee

J'ai ajoute un module dedie :

- `src/logging_config.py`

Son role est de configurer explicitement le logging du projet.

Concretement, il :

- cree le dossier `outputs/logs/` si besoin
- cree le fichier `outputs/logs/pipeline.log`
- attache un `FileHandler` au logger racine
- applique un format lisible avec date, niveau, nom du module et message

### Pourquoi cette approche est propre

Cette solution respecte les contraintes d'architecture du projet :

- `run_pipeline.py` reste minimal
- la configuration du logging est dans un module dedie
- `src/pipeline.py` active cette configuration au demarrage
- les modules metier continuent d'utiliser simplement `logger = logging.getLogger(__name__)`

Autrement dit :

- `logging_config.py` configure
- `pipeline.py` demarre
- les autres modules journalisent

### Ou se trouvent maintenant les logs

Les logs sont maintenant ecrits dans :

- `outputs/logs/pipeline.log`

Cela est coherent avec le reste de ton projet :

- `outputs/ingestion/` contient les donnees produites
- `outputs/logs/` contient les traces d'execution

### Ce que cela t'apprend pour la suite

Il faut retenir une idee tres importante :

- `logger.info(...)` = emettre un message
- `FileHandler` ou configuration logging = definir ou ce message sera stocke

Dans les vrais projets, cette distinction est essentielle.

Sans configuration de logging :

- tu crois avoir des logs
- mais rien n'est persiste

Avec une vraie configuration :

- tes messages deviennent exploitables
- tu peux auditer une execution
- tu peux deboguer plus facilement
- tu peux superviser ton pipeline dans le temps

## 13. Phase de transformation des donnees

Le pipeline contient maintenant une vraie phase de transformation apres l'ingestion.

L'objectif de cette etape est simple :

- partir des donnees brutes ingerees
- les nettoyer
- les standardiser
- produire un fichier exploitable pour les etapes suivantes

Le fichier genere est :

- `outputs/transformation/clean_sales_data.csv`

### Le role de `src/transformation/cleaning.py`

Ce module contient la logique metier de nettoyage.

Son role n'est pas :

- de decider quels fichiers Excel lire
- d'ecrire les sorties du pipeline

Son role est uniquement :

- de prendre un `DataFrame` d'entree
- d'appliquer les regles de nettoyage
- de renvoyer un `DataFrame` nettoye et un petit rapport qualite

Cette separation est importante :

- `ingestion` lit les donnees
- `transformation` nettoie les donnees
- `pipeline` orchestre les etapes

### Ce que j'ai verifie et ameliore dans `cleaning.py`

La logique que tu avais ecrite etait deja saine. Je l'ai surtout fiabilisee et rendue plus explicite.

#### 1. Validation des colonnes attendues

J'ai ajoute une verification des colonnes obligatoires avant le nettoyage.

Pourquoi ?

Si un `DataFrame` arrive sans colonne essentielle comme :

- `transaction_id`
- `transaction_date`
- `amount`

alors il vaut mieux lever une erreur claire tout de suite plutot que laisser le code echouer plus loin de maniere moins lisible.

#### 2. Gestion plus sure des colonnes texte

J'ai remplace plusieurs conversions `astype(str)` par `astype("string")`.

Pourquoi c'est mieux ?

- `astype(str)` transforme les valeurs manquantes en chaine `"nan"`
- `astype("string")` garde une vraie notion de valeur manquante pandas

Cela rend le nettoyage plus propre et plus previsible.

#### 3. Ajout de logs de transformation

J'ai ajoute des logs a chaque grande etape :

- debut du nettoyage
- apres filtrage des `transaction_id`
- apres conversion des types et filtre sur `amount`
- apres filtre sur `status`
- apres deduplication
- fin du nettoyage

Ces logs sont tres utiles pour comprendre rapidement :

- combien de lignes entrent dans la transformation
- combien sont eliminees par chaque regle
- combien restent a la fin

### Les regles de nettoyage actuellement appliquees

Le nettoyage effectue aujourd'hui les operations suivantes :

1. suppression des lignes sans `transaction_id` valide
2. standardisation des colonnes texte
3. conversion de `transaction_date` en date
4. conversion de `amount` en numerique
5. suppression des lignes avec date invalide
6. suppression des lignes avec montant nul, manquant ou negatif
7. conservation des seules lignes avec `status = ACTIVE`
8. suppression des doublons sur `transaction_id`
9. ajout de `month_start`
10. ajout de `year_month`

Ces deux nouvelles colonnes sont utiles pour les futures analyses mensuelles.

### Le `quality_report`

La fonction de nettoyage continue de retourner un objet `CleaningResult` avec :

- `data`
- `quality_report`

Le `quality_report` contient le nombre de lignes a differents stades.

Pour l'instant, le pipeline ne l'ecrit pas dans un fichier dedie, car ton besoin principal etait :

- obtenir `clean_sales_data.csv`
- disposer de logs clairs

Mais ce rapport pourra plus tard etre sauvegarde si tu veux renforcer le suivi qualite.

### Integration de la transformation dans `src/pipeline.py`

J'ai integre la transformation comme etape suivant l'ingestion.

Le flux est maintenant :

1. ingestion incrementale des nouveaux fichiers Excel
2. mise a jour de `business_data.csv`
3. chargement des donnees d'ingestion completes
4. appel a `clean_sales_data(...)`
5. sauvegarde de `clean_sales_data.csv`

### Pourquoi la transformation s'execute meme s'il n'y a aucun nouveau fichier

J'ai choisi de faire tourner la transformation meme quand l'ingestion n'a aucun nouveau fichier.

Pourquoi ce choix ?

- cela garantit que `clean_sales_data.csv` existe toujours
- cela garantit que la sortie de transformation reste reconstruisable a partir de `business_data.csv`
- cela decouple mieux la transformation de la detection incrementale des fichiers source

Autrement dit :

- l'ingestion est incrementale au niveau des fichiers Excel
- la transformation reconstruit la vue nettoyee a partir de la sortie d'ingestion actuelle

C'est un choix simple et sain pour ton projet actuel.

Plus tard, tu pourras rendre aussi la transformation incrementale si tu en as besoin.

### La sortie de transformation

Le pipeline ecrit maintenant :

- `outputs/transformation/clean_sales_data.csv`

Dans ton cas actuel, ce fichier contient :

- `22074` lignes nettoyees
- `11` colonnes

Les colonnes incluent maintenant :

- les colonnes d'origine nettoyees
- `month_start`
- `year_month`

### Les logs de transformation

La phase de transformation est maintenant visible dans :

- `outputs/logs/pipeline.log`

Tu peux y voir des messages comme :

- `Starting transformation stage on 32497 row(s)`
- `Rows after date/amount filters: 22074`
- `Rows after deduplication: 22074`
- `Transformation stage completed: 22074 cleaned row(s) written`

Cela rend le pipeline beaucoup plus facile a suivre et a deboguer.

### Ce que cette phase t'apprend

Cette etape montre une idee importante du data engineering :

- les donnees ingerees ne sont pas encore des donnees pretes a analyser

Il faut souvent une phase intermediaire de transformation pour :

- corriger les types
- filtrer les valeurs invalides
- harmoniser les formats
- enrichir les donnees avec des colonnes utiles

Cette separation entre ingestion et transformation est une tres bonne pratique, car elle rend le pipeline :

- plus lisible
- plus testable
- plus evolutif

### Ce que tu pourras faire ensuite

La prochaine suite logique, apres cette phase, serait par exemple :

- calculer des KPI a partir de `clean_sales_data.csv`
- produire des agregations mensuelles
- sauvegarder un rapport qualite de transformation
- ajouter des tests unitaires sur `clean_sales_data(...)`

## 14. Pourquoi le comportement actuel est coherent techniquement, mais pas ideal pour ce projet

Apres l'integration de la transformation, un point important est apparu :

- actuellement, la transformation se relance meme s'il n'y a aucun nouveau fichier Excel

Pour ton projet, ce n'est pas le comportement cible.

Tu veux profiter de l'incremental de bout en bout, donc :

- si aucun nouveau fichier n'est detecte
- alors la transformation ne doit pas se relancer non plus

### Pourquoi le comportement actuel reste coherent techniquement

Le comportement actuel vient d'un choix de simplicite :

- l'ingestion est incrementale
- mais la transformation est traitee comme une reconstruction complete a partir de `business_data.csv`

Autrement dit, le pipeline fait ceci :

1. il met a jour les donnees ingerees
2. puis il reconstruit la vue nettoyee complete

Cette approche est techniquement coherente parce qu'elle garantit que :

- `clean_sales_data.csv` peut toujours etre reconstruit a partir des donnees d'ingestion
- la logique de transformation reste simple
- on evite certains cas complexes lies a l'incremental cote nettoyage

Dans certains projets, ce choix est tout a fait acceptable.

### Pourquoi ce n'est pas ideal dans ton cas

Dans ton projet, l'objectif principal est justement :

- eviter le retraitement inutile
- reduire le temps d'execution
- profiter de l'incremental sur toute la chaine

Dans ce contexte, relancer la transformation alors qu'aucune nouvelle donnee n'est arrivee n'apporte rien.

Donc, meme si le comportement actuel est defendable techniquement, il n'est pas aligne avec le besoin fonctionnel du projet.

### Pourquoi la transformation incrementale est plus subtile que l'ingestion incrementale

L'ingestion incrementale est relativement simple :

- on detecte les nouveaux fichiers
- on lit uniquement ces fichiers

La transformation incrementale demande un peu plus de vigilance, car elle ne fait pas seulement de la lecture.

Elle applique aussi des regles metier comme :

- filtrage
- normalisation
- suppression de doublons

Par exemple, dans ton nettoyage, on dedoublonne sur `transaction_id`.

Cela veut dire que si un nouveau lot contient un `transaction_id` deja present dans `clean_sales_data.csv`, il faut savoir quoi faire :

- ignorer la nouvelle ligne
- remplacer l'ancienne
- garder la premiere

Ce point montre pourquoi la transformation incrementale demande plus de reflexion que l'ingestion incrementale.

### La direction cible pour ce projet

Pour ton projet, la bonne direction est la suivante :

1. detection des nouveaux fichiers Excel
2. ingestion uniquement des nouvelles donnees
3. si aucun nouveau fichier :
   pas de transformation
4. si de nouvelles donnees existent :
   transformation uniquement de ces nouvelles lignes
5. ajout des lignes nettoyees a `clean_sales_data.csv`
6. verification des doublons avec l'historique deja nettoye

Autrement dit :

- ingestion incrementale
- transformation incrementale

Cela permet de profiter de l'incremental de bout en bout.

### Ce qu'il faut retenir

Il faut bien distinguer deux choses :

- une solution techniquement coherente
- une solution adaptee a ton objectif

La reconstruction complete de la transformation est :

- simple
- robuste
- techniquement defendable

Mais pour ce projet, la meilleure solution est une transformation incrementale, car elle est plus coherente avec ton objectif principal :

- ne rien retraiter inutilement

### Ce qui sera implemente ensuite

La suite logique sera donc de faire evoluer le pipeline pour que :

- s'il n'y a aucun nouveau fichier, la transformation ne s'execute pas
- s'il y a de nouvelles lignes, seules ces lignes soient nettoyees
- `clean_sales_data.csv` soit mis a jour incrementalement

Cela rendra le pipeline plus proche d'un vrai pipeline incremental de production.

## 15. Implementation finale de la transformation incrementale

La transformation incrementale a maintenant ete implementee dans le pipeline.

Cette section decrit le comportement final, qui remplace le design intermediaire explique plus haut.

### Idee cle

Le pipeline ne decide plus de lancer la transformation uniquement a partir des fichiers Excel nouvellement ingeres pendant le run courant.

Il compare maintenant :

- les fichiers deja ingeres avec succes
- les fichiers deja presents dans `clean_sales_data.csv`

La transformation traite uniquement les fichiers qui sont :

- deja ingeres
- mais pas encore transformes

### Pourquoi cette approche est meilleure

Cette logique est plus robuste que :

- "transformer tout"
- ou "transformer seulement les fichiers ingeres pendant ce run"

Pourquoi ?

Parce qu'elle gere aussi les cas de rattrapage.

Exemple concret dans ton projet :

- les fichiers `2019-05.xls` et `2019-06.xls` avaient deja ete ingeres
- mais ils n'etaient pas encore presents dans `clean_sales_data.csv`

Avec la nouvelle logique, le pipeline a pu :

- detecter qu'ils etaient deja ingeres
- voir qu'ils n'etaient pas encore transformes
- les nettoyer
- les ajouter a la sortie de transformation

Cela permet de remettre le pipeline dans un etat coherent sans retraiter toute l'historique.

### Comment le pipeline determine les fichiers a transformer

Le pipeline utilise deux sources d'information :

1. `outputs/ingestion/ingestion_metadata.csv`
   pour savoir quels fichiers ont ete charges avec succes
2. `outputs/transformation/clean_sales_data.csv`
   pour savoir quels fichiers ont deja produit des lignes nettoyees

Comme `clean_sales_data.csv` conserve :

- `source_file`
- `source_folder`

on peut retrouver tres simplement la liste des fichiers deja transformes.

Le pipeline calcule ensuite :

- fichiers ingeres
- moins
- fichiers deja transformes

Le resultat correspond aux fichiers restant a transformer.

### Le comportement final du pipeline

Le pipeline suit maintenant cette logique :

1. detection des nouveaux fichiers Excel a ingerer
2. ingestion incrementale des nouveaux fichiers uniquement
3. lecture de l'etat de transformation actuel
4. identification des fichiers ingeres mais non encore transformes
5. transformation uniquement des lignes venant de ces fichiers
6. ajout des lignes nettoyees a `clean_sales_data.csv`

### Ce qui se passe s'il n'y a aucun nouveau fichier

Il faut distinguer deux cas.

#### Cas 1 : aucun nouveau fichier et aucune transformation en retard

Dans ce cas :

- l'ingestion est sautee
- la transformation est sautee

Le pipeline ne refait aucun travail inutile.

C'est le comportement incremental cible en regime nominal.

#### Cas 2 : aucun nouveau fichier, mais certaines donnees ne sont pas encore transformees

Dans ce cas :

- l'ingestion reste sautee
- la transformation traite seulement les fichiers en retard

Ce cas correspond a une mise a niveau de l'etat du pipeline.

Une fois ce rattrapage termine, les runs suivants ne relanceront plus la transformation tant qu'aucun nouveau fichier n'apparait.

### Deduplication entre lots

Le nettoyage dedoublonne deja les lignes a l'interieur d'un lot avec :

- `transaction_id`

J'ai ajoute en plus une protection au moment de l'append dans `clean_sales_data.csv` :

- si un `transaction_id` nettoye existe deja dans la sortie finale
- la nouvelle ligne est ignoree

Cela permet d'eviter d'introduire des doublons entre plusieurs runs incrementaux.

### Correction importante sur les dates

J'ai aussi corrige un point subtil dans `cleaning.py`.

Quand les donnees venaient de CSV deja ecrits par le pipeline, la colonne `transaction_date` pouvait contenir des formats mixtes comme :

- `2019-01-01`
- `2019-03-01 00:00:00`

J'ai donc utilise :

```python
pd.to_datetime(..., format="mixed", errors="coerce")
```

Pourquoi ?

Sans cela, pandas pouvait mal parser une partie des dates et eliminer a tort certaines lignes lors du nettoyage.

### Ce que cette implementation t'apprend

Cette version finale montre une idee tres importante :

- un pipeline incremental ne doit pas seulement detecter les nouvelles donnees
- il doit aussi suivre l'etat d'avancement de chaque etape

Dans ton projet :

- l'etat d'ingestion est porte par `ingestion_metadata.csv`
- l'etat de transformation est deduit a partir de `clean_sales_data.csv`

Cela te donne deja une petite architecture de pipeline tres proche de vraies pratiques de production.

## 16. Phase analytics : calcul des KPIs en incremental

Le pipeline contient maintenant une phase analytics apres la transformation.

Son objectif est de :

- partir des donnees nettoyees
- calculer des indicateurs metier utiles
- sauvegarder plusieurs sorties CSV dans `outputs/analytics/`
- n'executer le calcul des KPIs que lorsque des fichiers restent a analyser

### Les sorties analytics maintenant generees

Le pipeline ecrit desormais les fichiers suivants dans `outputs/analytics/` :

- `kpi_overview.csv`
- `monthly_kpis.csv`
- `kpis_by_store.csv`
- `kpis_by_plan.csv`
- `analytics_quality.csv`
- `analytics_file_inventory.csv`

### Le role de `src/analytic/kpis.py`

Ce module contient la logique metier de calcul des indicateurs.

Comme pour les autres etapes, son role n'est pas :

- de lire les fichiers Excel
- de decider quels fichiers sont nouveaux
- de gerer directement l'orchestration du pipeline

Son role est :

- de prendre un lot de donnees nettoyees
- de normaliser les types utiles au calcul
- de produire un ensemble de sorties KPI

### Ce que j'ai corrige et ameliore dans `kpis.py`

#### 1. Validation des colonnes attendues

J'ai ajoute une verification des colonnes necessaires au calcul des KPIs.

Pourquoi ?

Parce que les KPIs reposent sur des colonnes obligatoires comme :

- `transaction_id`
- `transaction_date`
- `amount`
- `store`
- `plan`
- `month_start`
- `year_month`

Si l'une d'elles manque, il vaut mieux lever une erreur claire plutot que produire des resultats faux ou incomplets.

#### 2. Normalisation robuste des types

Les donnees KPI sont relues depuis `clean_sales_data.csv`.

Donc, meme si elles etaient propres a l'etape de transformation, certaines colonnes reviennent depuis CSV sous forme de chaines, notamment :

- `transaction_date`
- `month_start`

J'ai donc ajoute une normalisation explicite avant les agregations :

- conversion des dates avec `pd.to_datetime(..., format="mixed")`
- conversion de `amount` en numerique
- nettoyage de certaines colonnes texte

Cela evite les erreurs silencieuses dans les calculs.

#### 3. Ajout de logs pour la phase KPI

Le module analytics journalise maintenant :

- le debut du calcul des KPIs
- la taille du lot traite
- le nombre de lignes produites pour les sorties mensuelles, magasins et plans

Ces logs s'ajoutent a ceux du pipeline, qui journalise aussi :

- combien de fichiers restent a analyser
- quand les sorties KPI sont ecrites
- quand l'etape analytics est sautee

### Les KPIs calcules et leur signification business

#### `kpi_overview.csv`

Ce fichier contient une vue de synthese globale sur toute la periode analysee.

Les indicateurs calcules sont :

- `period_start`
  premiere date de transaction presente dans les donnees analysees
- `period_end`
  derniere date de transaction presente dans les donnees analysees
- `total_revenue`
  chiffre d'affaires total sur la periode
- `total_transactions`
  nombre total de transactions uniques
- `average_ticket`
  panier moyen, c'est-a-dire le chiffre d'affaires moyen par transaction
- `new_revenue`
  chiffre d'affaires genere par les nouveaux contrats
- `existing_revenue`
  chiffre d'affaires genere par les contrats existants
- `new_revenue_share`
  part du chiffre d'affaires venant des nouveaux contrats
- `stores_count`
  nombre de magasins distincts actifs dans les donnees

Fonctionnellement, ce fichier sert a repondre rapidement a des questions comme :

- combien avons-nous vendu au total ?
- quelle est la taille moyenne d'une transaction ?
- la croissance vient-elle plutot de nouveaux clients ou du portefeuille existant ?

#### `monthly_kpis.csv`

Ce fichier donne une vue mensuelle de la performance.

Les indicateurs calcules sont :

- `revenue_existing`
  chiffre d'affaires mensuel provenant des contrats existants
- `revenue_new`
  chiffre d'affaires mensuel provenant des nouveaux contrats
- `revenue_total`
  chiffre d'affaires total du mois
- `transactions`
  nombre de transactions du mois
- `average_ticket`
  panier moyen du mois
- `growth_mom`
  croissance month-over-month, c'est-a-dire l'evolution du chiffre d'affaires par rapport au mois precedent

Fonctionnellement, ce fichier permet de voir :

- si le business progresse ou recule d'un mois a l'autre
- si certaines periodes sont plus fortes que d'autres
- si les ventes evoluent par volume ou par panier moyen

#### `kpis_by_store.csv`

Ce fichier agrege les KPIs par magasin.

Les indicateurs calcules sont :

- `revenue`
  chiffre d'affaires du magasin
- `transactions`
  nombre de transactions du magasin
- `average_ticket`
  panier moyen du magasin
- `revenue_share`
  part du chiffre d'affaires global generee par ce magasin

Fonctionnellement, cela permet de comparer les performances des magasins et d'identifier :

- les points de vente les plus contributeurs
- les magasins qui vendent beaucoup mais avec un faible panier moyen
- ceux qui ont un poids important dans le chiffre d'affaires total

#### `kpis_by_plan.csv`

Ce fichier agrege les KPIs par plan commercial (`Bronze`, `Silver`, `Gold`).

Les indicateurs calcules sont :

- `revenue`
  chiffre d'affaires genere par le plan
- `transactions`
  nombre de transactions du plan
- `average_ticket`
  panier moyen du plan
- `revenue_share`
  part du chiffre d'affaires global representee par ce plan

Fonctionnellement, cela permet de comprendre :

- quels plans contribuent le plus au revenu
- quels plans sont les plus vendus
- quels plans tirent le mieux le panier moyen vers le haut

#### `analytics_quality.csv`

Ce fichier conserve un petit rapport qualite par execution analytics.

Il contient par exemple :

- le nombre de lignes nettoyees recues en entree
- le nombre de fichiers traites dans le batch
- le nombre de mois couverts
- le nombre de lignes generees dans les differentes sorties KPI
- la periode couverte
- un `run_timestamp`

Fonctionnellement, il aide a auditer les runs analytics.

#### `analytics_file_inventory.csv`

Ce fichier est la memoire incremental de l'etape KPI.

Il enregistre pour chaque fichier source :

- son nom
- son dossier
- le nombre de lignes analysees
- la periode couverte
- le statut

Ce fichier permet au pipeline de savoir quels fichiers ont deja ete pris en compte dans les KPIs.

### Comment l'incremental KPI fonctionne

Le pipeline ne recalcule pas les KPIs a chaque execution.

Il compare :

- les fichiers deja presents dans `clean_sales_data.csv`
- les fichiers deja presents dans `analytics_file_inventory.csv`

Puis il calcule :

- fichiers nettoyes
- moins
- fichiers deja analyses

Le resultat correspond aux fichiers restant a analyser.

### Le comportement final de l'etape analytics

#### Cas 1 : aucun fichier en attente d'analyse

Dans ce cas :

- l'etape analytics est sautee
- aucun fichier KPI n'est reecrit

Cela evite tout recalcul inutile.

#### Cas 2 : un ou plusieurs fichiers sont en attente

Dans ce cas :

- seules les lignes nettoyees de ces fichiers sont prises en compte dans le batch analytics
- les sorties KPI existantes sont mises a jour incrementalement
- l'inventaire analytics est enrichi

### Comment les KPI sont mis a jour incrementalement

Le principe n'est pas de recalculer tous les KPIs depuis zero.

Le pipeline fait plutot ceci :

- il calcule un lot KPI sur les nouvelles lignes nettoyees
- il fusionne ce lot avec les sorties KPI deja existantes
- il recalcule seulement les colonnes derivees necessaires

Exemples :

- les revenus mensuels sont ajoutes au bon mois
- les KPIs par magasin sont mis a jour en additionnant les nouveaux revenus et transactions
- les KPIs par plan sont mis a jour de la meme maniere
- les parts de revenu et paniers moyens sont recalcules a partir des agregats mis a jour

### Un point subtil sur l'incremental analytics

Pour certains indicateurs, une vraie mise a jour incremental est assez naturelle :

- revenus
- volumes
- transactions

Pour d'autres, il faut recalculer une valeur derivee a partir des totaux mis a jour, par exemple :

- `average_ticket`
- `revenue_share`
- `growth_mom`

Cela reste incremental, car on ne repart pas des transactions brutes historiques.

On repart des tables KPI deja agregees, puis on met a jour les colonnes derivees.

### Ce que cette phase t'apprend

Avec cette etape KPI, tu vois maintenant trois niveaux differents d'incremental dans un meme projet :

- ingestion incremental par fichier brut
- transformation incrementale par fichier nettoye restant a traiter
- analytics incremental par fichier deja transforme mais pas encore analyse

Cela te rapproche beaucoup d'une vraie architecture de pipeline data.

### Ce que tu pourras faire ensuite

La suite logique pourrait etre :

- ajouter des tests sur les calculs KPI
- produire des dashboards ou exports Excel a partir des CSV analytics
- ajouter des KPI supplementaires
  par exemple : taux de retention, repartition geographique, KPI par type de contrat, top evolutions mensuelles
