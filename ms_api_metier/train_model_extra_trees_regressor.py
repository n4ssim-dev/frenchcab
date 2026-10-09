""" Comparaison entre RandomForest et ExtraTreesRegressor 
ExtraTreesRegressor est un algorithme de Machine Learning supervisé qui
utilise plusieurs arbres de décision pour prédire une valeur numérique.
Dans ce projet, il sert à prédire la durée d'un trajet en taxi, en minutes,
à partir de variables comme la distance, l'heure de départ, les zones géographiques 
et les indicateurs de trafic.
"""
import duckdb
import joblib
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# 1. CONFIGURATION
# ============================================================

DB_PATH = "data/yellow_taxi.db"
MODEL_PATH = "models/model_duree_extra_trees.joblib"

os.makedirs("models", exist_ok=True)

# ============================================================
# 2. EXTRACTION DES DONNEES
# ============================================================

con = duckdb.connect(DB_PATH, read_only=True)

df = con.execute("""
SELECT
    f.duree_minutes, f.distance, f.nb_passagers, f.id_vendeur,
    f.id_tarif, f.id_location_depart, f.id_location_arrivee,
    t.date_heure, t.heure, t.creneau_jour,
    t.jour_semaine, t.est_weekend,
    ld.arrondissement AS arr_depart,
    la.arrondissement AS arr_arrivee,
    ld.zone_service AS sz_depart,
    la.zone_service AS sz_arrivee,
    fc.nb_lag1, fc.nb_lag2, fc.nb_lag_1j, fc.nb_roll_3h,
    fc.lenteur_lag1, fc.lenteur_lag_1j,
    fc.lenteur_roll_3h, fc.lenteur_roll_24h
FROM fait_trajets f
JOIN dim_temps t
    ON f.id_temps_depart = t.id_temps
JOIN features_creneau fc
    ON f.id_temps_depart = fc.id_temps
JOIN dim_location ld
    ON f.id_location_depart = ld.id_location
JOIN dim_location la
    ON f.id_location_arrivee = la.id_location
WHERE f.duree_minutes BETWEEN 1 AND 180
  AND f.distance BETWEEN 0.1 AND 80
  AND t.date_heure >= (
      SELECT MIN(date_heure) FROM dim_temps
  ) + INTERVAL 1 DAY
""").df()

con.close()

print(f"Nombre de lignes : {len(df)}")


# ============================================================
# 3. MATRICE DE CORRELATION
# ============================================================

print("\n1. Matrice de correlation du modéle Extra Trees Regressors")
print("-" * 50)

dossier_sortie = "data/Matrices_correlation/"
os.makedirs(dossier_sortie, exist_ok=True)

corr = df.corr(numeric_only=True)
print(corr)

plt.figure(figsize=(14, 12))
plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
plt.colorbar(label="Correlation")

plt.xticks(
    range(len(corr.columns)),
    corr.columns,
    rotation=45,
    ha="right"
)
plt.yticks(range(len(corr.columns)), corr.columns)

for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        plt.text(
            j, i, f"{corr.iloc[i, j]:.2f}",
            ha="center", va="center", fontsize=7
        )

plt.title("Matrice de correlation - Duree trajet")
plt.tight_layout()

plt.savefig(
    os.path.join(
        dossier_sortie,
        "Matrice_correlation_duree_trajet_ExtraTreesRegressor.png"
    ),
    dpi=120
)

plt.savefig("Matrice_correlation_duree_trajet_ExtraTreesRegressor.png", dpi=150, bbox_inches="tight")
plt.close()


# ============================================================
# 4. PREPARATION DES VARIABLES
# ============================================================

print("\n2. Preparation des variables")
print("-" * 50)

df["meme_zone"] = (
    df["id_location_depart"] == df["id_location_arrivee"]
).astype(int)

df["est_weekend"] = df["est_weekend"].astype(int)

df["trajet_aeroport"] = (
    df[["sz_depart", "sz_arrivee"]]
    .isin(["Airports", "EWR"])
    .any(axis=1)
    .astype(int)
)

# Encodage cyclique des 48 creneaux de 30 minutes
df["creneau_sin"] = np.sin(
    2 * np.pi * df["creneau_jour"] / 48
)

df["creneau_cos"] = np.cos(
    2 * np.pi * df["creneau_jour"] / 48
)


# ============================================================
# 5. DECOUPAGE TEMPOREL : 80 % TRAIN / 20 % TEST
# ============================================================

date_coupure = df["date_heure"].quantile(0.8)

train = df[
    df["date_heure"] <= date_coupure
].drop(columns="date_heure").copy()

test = df[
    df["date_heure"] > date_coupure
].drop(columns="date_heure").copy()


# Encodage des variables categorielles
colonnes_cat = [
    "arr_depart",
    "arr_arrivee",
    "sz_depart",
    "sz_arrivee"
]

train = pd.get_dummies(
    train,
    columns=colonnes_cat,
    dtype=int
)

test = pd.get_dummies(
    test,
    columns=colonnes_cat,
    dtype=int
)

# Meme colonnes et meme ordre pour train et test
test = test.reindex(
    columns=train.columns,
    fill_value=0
)


# Remplacement des valeurs manquantes
# Les medianes sont calculees uniquement sur train
mediane = train.median()

train = train.fillna(mediane)
test = test.fillna(mediane)


# Separation des variables explicatives et de la cible
X_train = train.drop(columns="duree_minutes")
y_train = train["duree_minutes"]

X_test = test.drop(columns="duree_minutes")
y_test = test["duree_minutes"]

print(f"Nombre de variables : {X_train.shape[1]}")
print(f"Train : {len(X_train)} lignes")
print(f"Test  : {len(X_test)} lignes")
print(f"Date de coupure : {date_coupure}")


# ============================================================
# 6. DEFINITION DES DEUX MODELES
# ============================================================

print("\n3. Initialisation des modeles")
print("-" * 50)

modeles = {
    "Random Forest": RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    )
}


# ============================================================
# 7. ENTRAINEMENT ET EVALUATION
# ============================================================

resultats = {}
predictions = {}

for nom, modele in modeles.items():

    print(f"\nEntrainement : {nom}")
    print("-" * 40)

    # Entrainement
    modele.fit(X_train, y_train)

    # Predictions sur le meme jeu de test
    y_pred = modele.predict(X_test)
    predictions[nom] = y_pred

    # Metriques
    mae = mean_absolute_error(y_test, y_pred)

    rmse = np.sqrt(
        mean_squared_error(y_test, y_pred)
    )

    r2 = r2_score(y_test, y_pred)

    resultats[nom] = {
        "MAE (min)": mae,
        "RMSE (min)": rmse,
        "R2": r2
    }

    print(f"MAE  : {mae:.3f} minutes")
    print(f"RMSE : {rmse:.3f} minutes")
    print(f"R2   : {r2:.4f}")


# ============================================================
# 8. COMPARAISON DES RESULTATS
# ============================================================

print("\n4. Comparaison des modeles")
print("=" * 65)

df_resultats = pd.DataFrame(resultats).T

print(df_resultats.round(4).to_string())

# Classement selon la MAE, la plus faible en premier
df_classement = df_resultats.sort_values(
    by="MAE (min)",
    ascending=True
)

meilleur_nom = df_classement.index[0]
meilleur_model = modeles[meilleur_nom]

print("\nMeilleur modele selon la MAE :")
print(meilleur_nom)

print(
    f"MAE  : {df_resultats.loc[meilleur_nom, 'MAE (min)']:.3f} min"
)
print(
    f"RMSE : {df_resultats.loc[meilleur_nom, 'RMSE (min)']:.3f} min"
)
print(
    f"R2   : {df_resultats.loc[meilleur_nom, 'R2']:.4f}"
)


# ============================================================
# 9. COMPARAISON AVEC LE MODELE NAIF
# ============================================================

print("\n5. Modele naif")
print("-" * 50)

y_naif = np.full(len(y_test), y_train.mean())

mae_naif = mean_absolute_error(y_test, y_naif)
rmse_naif = np.sqrt(mean_squared_error(y_test, y_naif))
r2_naif = r2_score(y_test, y_naif)

print(f"MAE  naive : {mae_naif:.3f} min")
print(f"RMSE naive : {rmse_naif:.3f} min")
print(f"R2 naive   : {r2_naif:.4f}")


# ============================================================
# 10. IMPORTANCE DES VARIABLES DU MEILLEUR MODELE
# ============================================================

print("\n6. Importance des variables")
print("-" * 50)

importances = (
    pd.Series(
        meilleur_model.feature_importances_,
        index=X_train.columns
    )
    .sort_values(ascending=False)
)

print(f"Modele analyse : {meilleur_nom}")
print("\nTop 10 variables :")
print(importances.head(10).round(4))


# Importance totale des variables de trafic selectionnees
trafic = importances[
    importances.index.str.startswith(
        ("lenteur_", "nb_lag", "nb_roll")
    )
]

print(
    f"\nImportance totale du trafic : {trafic.sum():.4f}"
)
print(trafic.round(4))


# ============================================================
# 11. GRAPHIQUE DE COMPARAISON DES MAE
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    df_resultats.index,
    df_resultats["MAE (min)"]
)

plt.axhline(
    mae_naif,
    linestyle="--",
    label="Modele naif"
)

plt.ylabel("MAE (minutes)")
plt.title("Comparaison des modeles - Duree des trajets")
plt.legend()
plt.tight_layout()

plt.savefig(
    "data/comparaison_modeles_duree.png",
    dpi=120
)

plt.show()
plt.close()


# ============================================================
# 12. SAUVEGARDE DU MEILLEUR MODELE
# ============================================================

artefact = {
    "model": meilleur_model,
    "nom_modele": meilleur_nom,
    "colonnes": list(X_train.columns),
    "mediane": mediane,
    "metriques": df_resultats.loc[meilleur_nom].to_dict()
}

joblib.dump(artefact, MODEL_PATH)

print(f"\nMeilleur modele sauvegarde : {MODEL_PATH}")
print(f"Modele retenu : {meilleur_nom}")
