import sys
from pathlib import Path

import yaml

ML_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ML_DIR))
from evaluation_model import main_evaluation

if __name__ == "__main__":
    p = yaml.safe_load(open(ML_DIR.parent / "params.yaml"))["evaluate"]
    main_evaluation(p["date_debut"], p["seuil_mae_minutes"])
