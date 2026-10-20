"""Promeut le dernier modele entraine s'il bat le champion actuel du registre.

Usage (depuis ms_api_metier) :
    python ml/promote_if_better.py              # compare et promeut si meilleur
    python ml/promote_if_better.py --dry-run    # compare sans rien enregistrer
    python ml/promote_if_better.py --marge 0.05 # exige 0.05 min de MAE en moins
"""
import argparse
import subprocess
import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))
from mlflow_utils import EXPERIENCE, init_mlflow

NOM_REGISTRE = "frenchcab-duree-trajet"


def dernier_run(etape):
    runs = mlflow.search_runs(
        experiment_names=[EXPERIENCE],
        filter_string=f"tags.etape = '{etape}' and attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
        output_format="list",
    )
    return runs[0] if runs else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--marge", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    init_mlflow()
    client = MlflowClient()

    run_train = dernier_run("train")
    if run_train is None:
        sys.exit("Aucun run d'entrainement trouve : lancer dvc repro d'abord")
    candidat = run_train.data.metrics["premier.mae_minutes"]
    print(f"Candidat : MAE {candidat:.3f} min (run {run_train.info.run_id[:8]})")

    run_eval = dernier_run("evaluate")
    seuil_ok = True
    if run_eval is not None:
        seuil_ok = run_eval.data.metrics.get("premier.seuil_respecte", 1.0) == 1.0
        print(f"Seuil de MAE respecte a l'evaluation : {seuil_ok}")

    mae_champion = None
    try:
        version = client.get_model_version_by_alias(NOM_REGISTRE, "champion")
        mae_champion = client.get_run(version.run_id).data.metrics.get("mae_minutes")
        print(f"Champion : version {version.version}, MAE {mae_champion} min")
    except Exception:
        print("Pas de champion actuel dans le registre")

    meilleur = mae_champion is None or candidat < mae_champion - args.marge
    promouvoir = meilleur and seuil_ok
    print("Decision :", "PROMOUVOIR" if promouvoir else "ne pas promouvoir")

    if args.dry_run:
        return
    resultat = "promu" if promouvoir else "non_promu"
    client.set_tag(run_train.info.run_id, "promotion", resultat)
    if promouvoir:
        subprocess.run(
            [sys.executable, str(ML_DIR / "register_model.py"), "--modele", "premier"],
            check=True,
        )


if __name__ == "__main__":
    main()
