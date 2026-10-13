import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error

# charge un nouveau dataset TLC
# appelle le pipeline de prédiction existant
# calcule une nouvelle MAE
# compare avec un seuil

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "yellow_taxi.db"
MODEL_PATH = DATA_DIR / "models" / "model_duree_extra_trees.joblib"
RESULTAT_PATH = DATA_DIR / "evaluation" / "evaluation.json"

COLONNES_CAT = ["arr_depart", "arr_arrivee", "sz_depart", "sz_arrivee"]

QUERY = """
SELECT
    f.duree_minutes, f.distance, f.nb_passagers, f.id_vendeur,
    f.id_tarif, f.id_location_depart, f.id_location_arrivee,
    t.date_heure, t.heure, t.creneau_jour, t.jour_semaine, t.est_weekend,
    ld.arrondissement AS arr_depart, la.arrondissement AS arr_arrivee,
    ld.zone_service AS sz_depart, la.zone_service AS sz_arrivee,
    fc.nb_lag1, fc.nb_lag2, fc.nb_lag_1j, fc.nb_roll_3h,
    fc.lenteur_lag1, fc.lenteur_lag_1j,
    fc.lenteur_roll_3h, fc.lenteur_roll_24h
FROM fait_trajets f
JOIN dim_temps t         ON f.id_temps_depart     = t.id_temps
JOIN features_creneau fc ON f.id_temps_depart     = fc.id_temps
JOIN dim_location ld     ON f.id_location_depart  = ld.id_location
JOIN dim_location la     ON f.id_location_arrivee = la.id_location
WHERE f.duree_minutes BETWEEN 1 AND 180
  AND f.distance BETWEEN 0.1 AND 80
  AND t.date_heure >= ?
"""


def charger_donnees_evaluation(date_debut):
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base introuvable : {DB_PATH}")

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = con.execute(QUERY, [date_debut]).df()

    if df.empty:
        raise ValueError(f"Aucun trajet à partir du {date_debut}")
    return df

def preparer_donnees_evaluation(df, bundle):
    df = df.copy()

    df["meme_zone"] = (df["id_location_depart"] == df["id_location_arrivee"]).astype(int)
    df["est_weekend"] = df["est_weekend"].astype(int)
    df["trajet_aeroport"] = (df[["sz_depart", "sz_arrivee"]].isin(["Airports", "EWR"]).any(axis=1).astype(int))
    df["creneau_sin"] = np.sin(2 * np.pi * df["creneau_jour"] / 48)
    df["creneau_cos"] = np.cos(2 * np.pi * df["creneau_jour"] / 48)

    df = df.drop(columns="date_heure")
    df = pd.get_dummies(df, columns=COLONNES_CAT, dtype=int)

    y = df["duree_minutes"]
    X = df.reindex(columns=bundle["colonnes"], fill_value=0)
    X = X.fillna(bundle["mediane"])
    return X, y


def evaluer_modele(date_debut):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")

    bundle = joblib.load(MODEL_PATH)
    df = charger_donnees_evaluation(date_debut)
    X, y = preparer_donnees_evaluation(df, bundle)

    y_pred = bundle["model"].predict(X)
    mae = mean_absolute_error(y, y_pred)

    return {
        "fichier_modele": MODEL_PATH.name,
        "algorithme": type(bundle["model"]).__name__,
        "date_debut_donnees": date_debut,
        "nb_trajets": len(y),
        "mae_minutes": round(float(mae), 3),
        "date_evaluation": datetime.now().isoformat(),
    }


def verifier_seuil(mae, seuil):
    return mae <= seuil


def main():
    DATE_DEBUT_EVALUATION = "2026-07-28"
    SEUIL_MAE_MINUTES = 6.0
    resultat = evaluer_modele(DATE_DEBUT_EVALUATION)
    resultat["seuil_minutes"] = SEUIL_MAE_MINUTES
    resultat["seuil_respecte"] = verifier_seuil(resultat["mae_minutes"], SEUIL_MAE_MINUTES)

    RESULTAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTAT_PATH, "w", encoding="utf-8") as f:
        json.dump(resultat, f, indent=4, ensure_ascii=False)

    print(json.dumps(resultat, indent=4, ensure_ascii=False))
    return 0 if resultat["seuil_respecte"] else 1

if __name__ == "__main__":
    sys.exit(main())