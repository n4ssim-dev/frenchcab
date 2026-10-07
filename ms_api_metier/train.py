import duckdb
import joblib
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DB_PATH = "data/yellow_taxi.db"
MODEL_PATH = "models/model_duree.joblib"

con = duckdb.connect(str(DB_PATH), read_only=True)
df = con.execute("""
SELECT
    f.duree_minutes, f.distance, f.nb_passagers, f.id_vendeur, f.id_tarif,
    f.id_location_depart, f.id_location_arrivee,
    t.date_heure, t.heure, t.creneau_jour, t.jour_semaine, t.est_weekend,
    ld.arrondissement AS arr_depart, la.arrondissement AS arr_arrivee,
    ld.zone_service  AS sz_depart,  la.zone_service  AS sz_arrivee,
    fc.nb_lag1, fc.nb_lag2, fc.nb_lag_1j, fc.nb_roll_3h,
    fc.lenteur_lag1, fc.lenteur_lag_1j,
    fc.lenteur_roll_3h, fc.lenteur_roll_24h
FROM fait_trajets f
JOIN dim_temps         t  ON f.id_temps_depart     = t.id_temps
JOIN features_creneau  fc ON f.id_temps_depart     = fc.id_temps
JOIN dim_location      ld ON f.id_location_depart  = ld.id_location
JOIN dim_location      la ON f.id_location_arrivee = la.id_location
WHERE f.duree_minutes BETWEEN 1 AND 180
  AND f.distance BETWEEN 0.1 AND 80
  AND t.date_heure >= (SELECT MIN(date_heure) FROM dim_temps) + INTERVAL 1 DAY
""").df()
con.close()


print(f"Nombre de lignes : {len(df)}")


print("\n1 : Matrice corrélation")
print("-" * 40)
dossier_sortie = "data/Matrices_correlation/"
os.makedirs(dossier_sortie, exist_ok=True)
corr = df.corr(numeric_only=True)

print(corr)

plt.figure(figsize=(14,12))

plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

plt.colorbar(label="Corrélation")

plt.xticks(range(len(corr.columns)), corr.columns, rotation=45)
plt.yticks(range(len(corr.columns)), corr.columns)

for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        plt.text(
            j,
            i,
            f"{corr.iloc[i, j]:.2f}",
            ha="center",
            va="center"
        )

plt.title("Matrice de corrélation Durée trajet")

plt.tight_layout()
plt.savefig(os.path.join(dossier_sortie, "Matrice_corrélation_duree_trajet.png"), dpi=120)
plt.show()
plt.close()


print("\n2 : Préparation des variables")
print("-" * 40)

df["meme_zone"] = (df["id_location_depart"] == df["id_location_arrivee"]).astype(int)
df["est_weekend"] = df["est_weekend"].astype(int)
df["trajet_aeroport"] = df[["sz_depart", "sz_arrivee"]].isin(["Airports", "EWR"]).any(axis=1).astype(int)
df["creneau_sin"] = np.sin(2 * np.pi * df["creneau_jour"] / 48)
df["creneau_cos"] = np.cos(2 * np.pi * df["creneau_jour"] / 48)

date_coupure = df["date_heure"].quantile(0.8)
train = df[df["date_heure"] <= date_coupure].drop(columns="date_heure")
test  = df[df["date_heure"] >  date_coupure].drop(columns="date_heure")

colonnes_cat = ["arr_depart", "arr_arrivee", "sz_depart", "sz_arrivee"]
train = pd.get_dummies(train, columns=colonnes_cat, dtype=int)
test  = pd.get_dummies(test,  columns=colonnes_cat, dtype=int).reindex(columns=train.columns, fill_value=0)

mediane = train.median()
train = train.fillna(mediane)
test  = test.fillna(mediane)

X_train, y_train = train.drop(columns="duree_minutes"), train["duree_minutes"]
X_test,  y_test  = test.drop(columns="duree_minutes"),  test["duree_minutes"]

print(f"Variables : {list(X_train.columns)}")
print(f"Train : {len(X_train)} lignes | Test : {len(X_test)} lignes")
print(f"Période train : jusqu'au {date_coupure}")



print("\n3 : Entraînement du Random Forest")
print("-" * 40)
rf = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42,
)
rf.fit(X_train, y_train)


print("\n4 : Évaluation")
print("-" * 40)
y_pred = rf.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
print(f"MAE  : {mae:.2f} min")
print(f"RMSE : {rmse:.2f} min")
print(f"R²   : {r2:.3f}")


mae_naif = mean_absolute_error(y_test, np.full(len(y_test), y_train.mean()))
print(f"MAE modèle naïf (moyenne) : {mae_naif:.2f} min")


importances = (pd.Series(rf.feature_importances_, index=X_train.columns)
               .sort_values(ascending=False))
print("\nTop 10 variables :")
print(importances.head(10).round(3))

joblib.dump({"model": rf, "colonnes": list(X_train.columns)}, MODEL_PATH)
print(f"\nModèle sauvegardé : {MODEL_PATH}")

trafic = importances[importances.index.str.startswith(("lenteur_", "nb_lag", "nb_roll"))]
print(f"\nPoids total des variables de trafic : {trafic.sum():.3f}")
print(trafic.round(3))