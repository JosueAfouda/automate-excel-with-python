# Runbook Ops

## Objet
Ce document explique comment exploiter le pipeline Python de reporting mensuel en contexte Windows/VM de service.

## Pré-requis
- Python 3.11 ou plus
- Accès en lecture au dossier `raw_sales_data/`
- Accès en écriture au dossier `outputs/`
- Droits d’exécution PowerShell sur les scripts du projet

## Arborescence attendue
```text
runtime-root/
  ├── config/
  │   └── prod.toml
  ├── raw_sales_data/
  ├── outputs/
  ├── scripts/
  └── .venv/
```

## Installation
Depuis la racine du projet :
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_runtime.ps1
```

## Vérification avant mise en production
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

Résultat attendu :
- `CHECK_STATUS=SUCCESS`
- présence du log par défaut
- détection des fichiers Excel d’entrée

## Lancement manuel
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_pipeline.ps1
```

Le script doit retourner :
- `PIPELINE_STATUS=SUCCESS`
- les chemins des sorties générées
- le fichier de log utilisé

## Logs
Le log par défaut est :
```text
outputs/logs/pipeline.log
```

Vérifier en priorité :
- `PIPELINE_STATUS`
- nombre de fichiers traités
- dernier mois couvert
- chemin du rapport final

## Rapport attendu
Le rapport métier de référence est :
```text
outputs/reports/rapport_ventes_latest.xlsx
```

## Tâche planifiée Windows
Exemple d’enregistrement :
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_scheduled_task.ps1
```

Ce script enregistre une tâche mensuelle locale. En environnement réel, adapter :
- le compte d’exécution
- l’heure de lancement
- le calendrier métier

## Procédure de relance
1. Corriger la cause de l’erreur.
2. Exécuter `check_environment.ps1`.
3. Relancer `run_pipeline.ps1`.
4. Vérifier `PIPELINE_STATUS=SUCCESS`.

## Diagnostic rapide
- Si `raw_sales_data/` est absent : erreur d’environnement ou de montage.
- Si aucun fichier Excel n’est trouvé : vérifier la zone de dépôt.
- Si le log n’est pas créé : vérifier les droits d’écriture dans `outputs/logs/`.
- Si le rapport n’est pas mis à jour : relire la fin de `pipeline.log`.
