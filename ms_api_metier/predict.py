from pathlib import Path
import duckdb
import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH =  "data/models/model_duree.joblib"
DB_PATH = BASE_DIR / "data" / "yellow_taxi.db"

# ---------------------------------------------------------
# Chargement unique : modèle + petites tables de référence
# ---------------------------------------------------------
bundle = joblib.load(MODEL_PATH)
model, COLONNES = bundle["model"], bundle["colonnes"]
MEDIANE = bundle.get("mediane")

if MEDIANE is None:
    print("Attention : pas de médianes dans le modèle, valeurs de repli à 0.")
    MEDIANE = pd.Series(0, index=COLONNES)

con = duckdb.connect(str(DB_PATH), read_only=True)
DIM_LOC = con.execute(
    "SELECT id_location, arrondissement, zone_service FROM dim_location"
).df().set_index("id_location")
FEAT_TRAFIC = con.execute(
    "SELECT * EXCLUDE (date_heure) FROM features_creneau"
).df()
con.close()

DEFAUTS = {"nb_passagers": 1, "id_vendeur": 2, "id_tarif": 1}


def construire_features(trajets: pd.DataFrame) -> pd.DataFrame:
    """
    trajets : colonnes obligatoires
        pickup (datetime), id_location_depart, id_location_arrivee, distance
      colonnes optionnelles (valeurs par défaut sinon)
        nb_passagers, id_vendeur, id_tarif
    """
    d = trajets.reset_index(drop=True).copy()
    for col, val in DEFAUTS.items():
        if col not in d:
            d[col] = val

    # --- Temps (grain 30 min, comme dim_temps) ---
    d["pickup"] = pd.to_datetime(d["pickup"])
    d["id_temps"] = d["pickup"].dt.floor("30min").dt.strftime("%Y%m%d%H%M").astype("int64")
    d["heure"] = d["pickup"].dt.hour
    d["creneau_jour"] = d["heure"] * 2 + d["pickup"].dt.minute // 30
    d["jour_semaine"] = d["pickup"].dt.dayofweek + 1            # 1 = lundi
    d["est_weekend"] = (d["jour_semaine"] >= 6).astype(int)
    d["mois"] = d["pickup"].dt.month                             # ignoré si absent du modèle
    d["creneau_sin"] = np.sin(2 * np.pi * d["creneau_jour"] / 48)
    d["creneau_cos"] = np.cos(2 * np.pi * d["creneau_jour"] / 48)

    # --- Zones ---
    inconnues = ~(d["id_location_depart"].isin(DIM_LOC.index)
                  & d["id_location_arrivee"].isin(DIM_LOC.index))
    if inconnues.any():
        raise ValueError(f"Zones inconnues sur les lignes : {list(d.index[inconnues])}")

    d["arr_depart"]  = d["id_location_depart"].map(DIM_LOC["arrondissement"])
    d["arr_arrivee"] = d["id_location_arrivee"].map(DIM_LOC["arrondissement"])
    d["sz_depart"]   = d["id_location_depart"].map(DIM_LOC["zone_service"])
    d["sz_arrivee"]  = d["id_location_arrivee"].map(DIM_LOC["zone_service"])
    d["meme_zone"] = (d["id_location_depart"] == d["id_location_arrivee"]).astype(int)
    d["trajet_aeroport"] = (
        d[["sz_depart", "sz_arrivee"]].isin(["Airports", "EWR"]).any(axis=1).astype(int)
    )
    d = pd.get_dummies(d, columns=["arr_depart", "arr_arrivee", "sz_depart", "sz_arrivee"], dtype=int)

    # --- Trafic (lags / rollings du créneau) ---
    d = d.merge(FEAT_TRAFIC, on="id_temps", how="left")

    # --- Alignement exact sur les colonnes d'entraînement ---
    X = d.reindex(columns=COLONNES, fill_value=0)
    return X.fillna(MEDIANE)


def predire_duree(trajets: pd.DataFrame) -> pd.Series:
    X = construire_features(trajets)
    return pd.Series(model.predict(X), name="duree_predite_min").round(1)


if __name__ == "__main__":
    exemples = pd.DataFrame([
        {"pickup": "2026-07-15 18:10", "id_location_depart": 162,
         "id_location_arrivee": 236, "distance": 3.2},
        {"pickup": "2026-07-17 8:35", "id_location_depart": 132,
         "id_location_arrivee": 230, "distance": 17.5, "nb_passagers": 2},
    ])
    exemples["duree_predite_min"] = predire_duree(exemples)
    print(exemples)