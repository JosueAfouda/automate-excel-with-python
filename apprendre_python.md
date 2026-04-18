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
