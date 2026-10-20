import json
import os
import subprocess
from pathlib import Path

import mlflow
import yaml

ROOT = Path(__file__).resolve().parent.parent
EXPERIENCE = "frenchcab-duree-trajet"


def init_mlflow():
    uri = os.environ.get("MLFLOW_TRACKING_URI") or f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}"
    mlflow.set_tracking_uri(uri)
    if mlflow.get_experiment_by_name(EXPERIENCE) is None:
        mlflow.create_experiment(EXPERIENCE, artifact_location=(ROOT / "mlruns").as_uri())
    mlflow.set_experiment(EXPERIENCE)


def _git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "inconnu"


def tags_tracabilite():
    tags = {
        "git_commit": _git("rev-parse", "HEAD"),
        "git_branche": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_modifications_non_commitees": str(_git("status", "--porcelain") != ""),
    }
    try:
        lock = yaml.safe_load(open(ROOT / "dvc.lock", encoding="utf-8"))
        for sortie in lock["stages"]["etl"]["outs"]:
            if sortie["path"].endswith("yellow_taxi.db"):
                tags["dvc_md5_yellow_taxi_db"] = sortie["md5"]
    except Exception:
        tags["dvc_md5_yellow_taxi_db"] = "inconnu"
    return tags


def derniere_ligne_json(chemin):
    lignes = [l for l in open(chemin, encoding="utf-8") if l.strip()]
    return json.loads(lignes[-1])
