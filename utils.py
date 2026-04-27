"""
Bibliothèque d'utilitaires génériques pour les projets Data Engineering en Python.
Ce module regroupe des fonctions réutilisables pour la gestion des chemins, 
la configuration, le logging, et le traitement incrémental de données avec Pandas.
"""

from __future__ import annotations

import functools
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar, cast

import pandas as pd

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

T = TypeVar("T")
logger = logging.getLogger(__name__)

# --- Utilitaires de Chemins et Système ---

def ensure_dir(path: Path | str) -> Path:
    """
    Assure que le répertoire parent du chemin donné existe.
    
    Args:
        path: Chemin du fichier ou du répertoire.
        
    Returns:
        Le chemin converti en Path.

    Exemple :
        >>> output_file = "outputs/reports/final_report.xlsx"
        >>> ensure_dir(output_file)
        >>> # Le dossier 'outputs/reports/' est maintenant créé sur le disque.
    """
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def resolve_path(path_str: str | None, base_dir: Path) -> Path | None:
    """
    Résout un chemin (absolu ou relatif à base_dir) et étend l'utilisateur (~).
    
    Args:
        path_str: La chaîne de chemin à résoudre.
        base_dir: Le répertoire de base pour les chemins relatifs.
        
    Returns:
        Le chemin résolu ou None si path_str est vide.

    Exemple :
        >>> base = Path("/home/user/project")
        >>> resolve_path("data/raw", base)
        PosixPath('/home/user/project/data/raw')
        >>> resolve_path("~/configs", base)
        PosixPath('/home/user/configs')
    """
    if not path_str:
        return None

    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = path.resolve()
    return path

# --- Utilitaires de Configuration et Logging ---

def load_toml(path: Path) -> dict[str, Any]:
    """
    Charge un fichier de configuration au format TOML.
    
    Args:
        path: Chemin vers le fichier TOML.
        
    Returns:
        Dictionnaire contenant la configuration.

    Exemple :
        >>> config = load_toml(Path("config/dev.toml"))
        >>> print(config['database']['host'])
        'localhost'
    """
    if not path.exists():
        logger.warning("Fichier de configuration introuvable : %s", path)
        return {}

    with path.open("rb") as f:
        return tomllib.load(f)

def setup_logging(
    log_file: Path | str | None = None,
    level: int = logging.INFO,
    log_format: str = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
) -> Path | None:
    """
    Configure le logging racine pour écrire dans un fichier et sur la console.
    
    Args:
        log_file: Chemin du fichier de log.
        level: Niveau de log (default: INFO).
        log_format: Format des messages de log.
        
    Returns:
        Le chemin du fichier de log résolu ou None.

    Exemple :
        >>> log_path = setup_logging(log_file="logs/pipeline.log")
        >>> logging.info("Démarrage du pipeline")
    """
    root_logger = logging.getLogger()
    # Nettoyage des handlers existants pour éviter les doublons lors de re-configurations
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(level)
    formatter = logging.Formatter(log_format)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    if log_file:
        p_log = Path(log_file).expanduser().resolve()
        p_log.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(p_log, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        return p_log
        
    return None

# --- Utilitaires Pandas et Data ---

def safe_read_csv(path: Path | str, **kwargs: Any) -> pd.DataFrame:
    """
    Lit un fichier CSV de manière sécurisée (retourne un DataFrame vide si absent).
    
    Args:
        path: Chemin du fichier CSV.
        **kwargs: Arguments passés à pd.read_csv.
        
    Returns:
        DataFrame chargé ou vide.

    Exemple :
        >>> df = safe_read_csv("outputs/ingestion_metadata.csv")
        >>> if df.empty:
        >>>     print("Premier run : aucune métadonnée trouvée.")
    """
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p, **kwargs)

def safe_read_excel(path: Path | str, **kwargs: Any) -> pd.DataFrame:
    """
    Lit un fichier Excel de manière sécurisée avec gestion d'erreurs.
    
    Args:
        path: Chemin du fichier Excel.
        **kwargs: Arguments passés à pd.read_excel.
        
    Returns:
        DataFrame chargé ou vide en cas d'erreur.

    Exemple :
        >>> df = safe_read_excel("raw_data/sales_2023_01.xlsx", sheet_name="Transactions")
        >>> print(f"{len(df)} lignes chargées.")
    """
    p = Path(path)
    try:
        return pd.read_excel(p, **kwargs)
    except Exception as e:
        logger.error("Erreur lors de la lecture de l'Excel %s : %s", p, e)
        return pd.DataFrame()

def normalize_columns(df: pd.DataFrame, required: list[str] | None = None) -> pd.DataFrame:
    """
    Normalise les noms de colonnes (minuscules, sans espaces) et assure la présence des colonnes requises.
    
    Args:
        df: DataFrame à normaliser.
        required: Liste des colonnes obligatoires à garantir.
        
    Returns:
        DataFrame normalisé.

    Exemple :
        >>> raw_df = pd.DataFrame(columns=["Transaction ID ", " Date"])
        >>> clean_df = normalize_columns(raw_df, required=["amount", "status"])
        >>> print(clean_df.columns)
        Index(['transaction id', 'date', 'amount', 'status'], dtype='object')
    """
    df_clean = df.copy()
    df_clean.columns = [str(c).strip().lower() for c in df_clean.columns]
    
    if required:
        for col in required:
            if col not in df_clean.columns:
                df_clean[col] = pd.NA
                
    return df_clean

def merge_and_deduplicate(
    dfs: list[pd.DataFrame], 
    subset: list[str] | None = None, 
    keep: str = "last"
) -> pd.DataFrame:
    """
    Combine plusieurs DataFrames et supprime les doublons.
    
    Args:
        dfs: Liste de DataFrames.
        subset: Colonnes pour la déduplication.
        keep: Quelle occurrence garder ('first', 'last', False).
        
    Returns:
        DataFrame combiné et dédupliqué.

    Exemple :
        >>> df_jan = pd.DataFrame({'id': [1, 2], 'val': ['A', 'B']})
        >>> df_feb = pd.DataFrame({'id': [2, 3], 'val': ['B_updated', 'C']})
        >>> merged = merge_and_deduplicate([df_jan, df_feb], subset=['id'], keep='last')
        >>> # L'id 2 aura la valeur 'B_updated'
    """
    valid_dfs = [df for df in dfs if not df.empty]
    if not valid_dfs:
        return pd.DataFrame()
        
    combined = pd.concat(valid_dfs, ignore_index=True)
    if subset:
        combined = combined.drop_duplicates(subset=subset, keep=keep)
        
    return combined

# --- Utilitaires ETL Incrémental ---

def get_file_keys(df: pd.DataFrame, folder_col: str, file_col: str) -> set[tuple[str, str]]:
    """
    Génère un ensemble de clés uniques (dossier, fichier) à partir d'un DataFrame.
    Utile pour identifier les fichiers déjà traités dans un pipeline.

    Args:
        df: DataFrame contenant les colonnes de suivi.
        folder_col: Nom de la colonne pour le dossier source.
        file_col: Nom de la colonne pour le nom du fichier.

    Returns:
        Ensemble de tuples (dossier, fichier).

    Exemple :
        >>> meta = pd.DataFrame({'folder': ['jan', 'jan'], 'file': ['s1.xlsx', 's2.xlsx']})
        >>> processed = get_file_keys(meta, 'folder', 'file')
        >>> print(processed)
        {('jan', 's1.xlsx'), ('jan', 's2.xlsx')}
    """
    if df.empty or folder_col not in df.columns or file_col not in df.columns:
        return set()
    
    return set(zip(df[folder_col].astype(str), df[file_col].astype(str)))

def filter_new_items(
    available_items: Iterable[T], 
    processed_keys: set[Any], 
    key_func: Callable[[T], Any]
) -> list[T]:
    """
    Filtre les éléments disponibles pour ne garder que ceux qui n'ont pas encore été traités.
    
    Args:
        available_items: Éléments à filtrer (ex: liste de Path).
        processed_keys: Clés (identifiants) déjà traitées.
        key_func: Fonction pour extraire la clé unique d'un élément.
        
    Returns:
        Liste des nouveaux éléments à traiter.

    Exemple :
        >>> files = [Path("data/f1.xlsx"), Path("data/f2.xlsx")]
        >>> processed = { "f1.xlsx" }
        >>> new_files = filter_new_items(files, processed, lambda p: p.name)
        >>> # new_files contient seulement [Path("data/f2.xlsx")]
    """
    return [item for item in available_items if key_func(item) not in processed_keys]

# --- Utilitaires de Performance et Monitoring ---

def execution_timer(func: Callable[..., T]) -> Callable[..., T]:
    """
    Décorateur pour mesurer et logger le temps d'exécution d'une fonction.

    Exemple :
        @execution_timer
        def heavy_processing(data):
            time.sleep(2)
            return data.upper()
        
        >>> heavy_processing("hello")
        # Log: Exécution de heavy_processing terminée en 2.0001 secondes
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info("Exécution de %s terminée en %.4f secondes", func.__name__, duration)
        return result
    return wrapper

def validate_runtime_env(required_dirs: list[Path]) -> bool:
    """
    Vérifie l'existence des répertoires critiques pour l'exécution d'un script.
    
    Args:
        required_dirs: Liste de chemins vers les dossiers obligatoires.

    Returns:
        True si tous existent, False sinon (avec logs d'erreurs).

    Exemple :
        >>> paths = [Path("data/raw"), Path("config")]
        >>> if not validate_runtime_env(paths):
        >>>     exit(1)
    """
    missing = [d for d in required_dirs if not d.exists()]
    if missing:
        for m in missing:
            logger.error("Répertoire requis manquant : %s", m)
        return False
    return True
