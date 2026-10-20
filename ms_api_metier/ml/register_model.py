"""Enregistre un modele dans le registre MLflow (a lancer a la main, hors pipeline DVC).

Usage (depuis ms_api_metier) :
    python ml/register_model.py                    # modele "premier" -> alias champion
    python ml/register_model.py --modele deuxieme  # modele "deuxieme" -> alias challenger

Le modele est copie dans mlruns/ (plusieurs Go) : a faire seulement pour un modele
que l'on veut promouvoir, pas a chaque entrainement.
"""
import argparse
import sys
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))
from mlflow_utils import ROOT, init_mlflow, tags_tracabilite

NOM_REGISTRE = "frenchcab-duree-trajet"
FICHIERS = {
    "premier": ROOT / "data" / "models" / "model_duree_premier.joblib",
    "deuxieme": ROOT / "data" / "models" / "model_duree_deuxieme.joblib",
}
ALIAS = {"premier": "champion", "deuxieme": "challenger"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modele", choices=FICHIERS, default="premier")
    args = parser.parse_args()

    chemin = FICHIERS[args.modele]
    if not chemin.exists():
        sys.exit(f"Modele introuvable : {chemin} (lancer dvc pull ou dvc repro)")

    print(f"Chargement de {chemin.name} ...")
    bundle = joblib.load(chemin)
    metriques = bundle.get("metriques") or bundle.get("metriques_deuxieme") or {}

    init_mlflow()
    with mlflow.start_run(run_name=f"registre-{args.modele}"):
        mlflow.set_tags({
            "etape": "register",
            "nom_modele": str(bundle.get("nom_modele")),
            "fichier_modele": chemin.name,
            **tags_tracabilite(),
        })
        if metriques:
            mlflow.log_metrics({
                "mae_minutes": float(metriques["MAE (min)"]),
                "rmse_minutes": float(metriques["RMSE (min)"]),
                "r2": float(metriques["R2"]),
            })
            mlflow.sklearn.log_model(
                bundle["model"],
                name="model",
                registered_model_name=NOM_REGISTRE,
                skops_trusted_types=["sklearn.tree._tree.Tree"],
            )

    client = MlflowClient()
    versions = client.search_model_versions(f"name='{NOM_REGISTRE}'")
    derniere = max(int(v.version) for v in versions)
    client.set_registered_model_alias(NOM_REGISTRE, ALIAS[args.modele], str(derniere))
    print(f"Modele enregistre : {NOM_REGISTRE} version {derniere}, alias '{ALIAS[args.modele]}'")
    print(f"Chargement : mlflow.sklearn.load_model('models:/{NOM_REGISTRE}@{ALIAS[args.modele]}')")


if __name__ == "__main__":
    main()
