# Test d'installation dans un venv propre

Ce scénario reproduit le travail d’un intégrateur ou d’un Ops qui vérifie qu’un package Python est installable et exécutable dans un environnement vierge.

## 1. Créer un nouvel environnement virtuel
```bash
python3 -m venv /tmp/sales-pipeline-venv
```

## 2. Activer le venv
```bash
source /tmp/sales-pipeline-venv/bin/activate
```

## 3. Mettre à jour pip
```bash
python -m pip install --upgrade pip
```

## 4. Installer le package depuis la racine du projet
```bash
python -m pip install .
```

## 5. Vérifier que la commande CLI est disponible
```bash
sales-pipeline --help
```

## 6. Vérifier le runtime
```bash
sales-pipeline check --config config/prod.toml --runtime-root .
```

Résultat attendu :
- `CHECK_STATUS=SUCCESS`
- un nombre de fichiers Excel détectés

## 7. Exécuter le pipeline
```bash
sales-pipeline run --config config/prod.toml --runtime-root .
```

Résultat attendu :
- `PIPELINE_STATUS=SUCCESS`
- affichage des sorties produites
- log dans `outputs/logs/pipeline.log`

## 8. Désactiver l’environnement
```bash
deactivate
```
