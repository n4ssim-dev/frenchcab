# charge l'artefact réellement utilisé
# lit nom_modele
# lit les métriques historiques
# fournit version/date

from pathlib import Path
import joblib
import json
import sklearn

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
MODELS_DIR = DATA_DIR / "models"

DB_PATH = DATA_DIR / "yellow_taxi.db"
MODEL_PATH = MODELS_DIR / "model_duree_extra_trees.joblib"

MODEL_VERSION = sklearn.__version__


# ============================================================
# CHARGEMENT DES INFORMATIONS DU MODELE
# ============================================================

def charger_infos_modele():

    artefact = joblib.load(MODEL_PATH)

    infos = {
        "fichier_modele": MODEL_PATH.name,
        "version": MODEL_VERSION,
        "nom_modele": artefact.get("nom_modele"),
        "metriques": artefact.get("metriques"),
        "nombre_features": len(artefact.get("colonnes", []))
    }

    return infos


# ============================================================
# AFFICHAGE
# ============================================================

def afficher_infos_modele():

    infos = charger_infos_modele()

    print(json.dumps(infos, indent=4, ensure_ascii=False))


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    charger_infos_modele()
    afficher_infos_modele()
