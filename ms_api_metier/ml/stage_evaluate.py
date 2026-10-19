import sys
from pathlib import Path

import mlflow
import yaml

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))
import evaluation_model as ev
from mlflow_utils import ROOT, derniere_ligne_json, init_mlflow, tags_tracabilite

PREFIXES = {"premier_modele": "premier", "deuxieme_modele": "deuxieme"}

if __name__ == "__main__":
    p = yaml.safe_load(open(ROOT / "params.yaml", encoding="utf-8"))["evaluate"]
    init_mlflow()
    with mlflow.start_run(run_name="evaluation"):
        mlflow.set_tags({"etape": "evaluate", **tags_tracabilite()})
        mlflow.log_params({"date_debut": p["date_debut"], "seuil_mae_minutes": p["seuil_mae_minutes"]})
        ev.main_evaluation(p["date_debut"], p["seuil_mae_minutes"])
        resultat = derniere_ligne_json(ev.RESULTAT_PATH)
        for cle, prefixe in PREFIXES.items():
            r = resultat[cle]
            mlflow.log_metric(f"{prefixe}.mae_minutes_eval", r["mae_minutes"])
            mlflow.log_metric(f"{prefixe}.nb_trajets_eval", r["nb_trajets"])
            mlflow.log_metric(f"{prefixe}.seuil_respecte", 1.0 if r["seuil_respecte"] else 0.0)
