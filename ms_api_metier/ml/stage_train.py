import sys
from pathlib import Path

import mlflow

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))
import train_ml_models as tm
from mlflow_utils import ROOT, derniere_ligne_json, init_mlflow, tags_tracabilite

PREFIXES = {"premier_modele": "premier", "deuxieme_modele": "deuxieme"}

if __name__ == "__main__":
    init_mlflow()
    with mlflow.start_run(run_name="entrainement"):
        mlflow.set_tags({"etape": "train", **tags_tracabilite()})
        estimateurs = tm.choix_modeles()
        tm.main_train()
        rapport = derniere_ligne_json(tm.EVALUATION_DIR / "rapport_entrainement_modeles.json")
        for cle, prefixe in PREFIXES.items():
            info = rapport[cle]
            mlflow.log_param(f"{prefixe}.nom_modele", info["nom_modele"])
            mlflow.log_param(f"{prefixe}.algorithme", info["algorithme"])
            estimateur = estimateurs.get(info["nom_modele"])
            if estimateur is not None:
                for nom, valeur in estimateur.get_params().items():
                    mlflow.log_param(f"{prefixe}.{nom}", str(valeur)[:500])
            for nom, valeur in info["metriques"].items():
                mlflow.log_metric(f"{prefixe}.{nom}", valeur)
        for fichier in [
            tm.DATA_DIR / "comparaison_modeles_duree.png",
            tm.EVALUATION_DIR / "rapport_entrainement_modeles.json",
            ROOT / "dvc.lock",
        ]:
            if fichier.exists():
                mlflow.log_artifact(str(fichier))
