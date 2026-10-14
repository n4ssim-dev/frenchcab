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
from pathlib import Path
import json
from datetime import datetime
import sklearn

# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"

DB_PATH = DATA_DIR / "yellow_taxi.db"
MODEL_PATH_1ST = MODELS_DIR / "model_duree_premier.joblib"
MODEL_PATH_2ND = MODELS_DIR / "model_duree_deuxieme.joblib"
MODEL_VERSION = sklearn.__version__
EVALUATION_DIR = DATA_DIR / "evaluation"
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

ML_DIR = BASE_DIR / "ml"

MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. EXTRACTION DES DONNEES
# ============================================================

def extraction_donnees():
    con = duckdb.connect(DB_PATH, read_only=True)

    try:
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

        con.commit()

        print(f"Nombre de lignes : {len(df)}")
    except duckdb.Error as erreur:
        print("Erreur SQLite :", erreur)
        con.rollback()

    finally:
        con.close()

    return df


# ============================================================
# 3. MATRICE DE CORRELATION
# ============================================================

def creation_matrice(df):

    print("\n1. Matrice de correlation du modéle Extra Trees Regressors")
    print("-" * 50)

    MATRICES_DIR = DATA_DIR / "Matrices_correlation"
    MATRICES_DIR.mkdir(parents=True, exist_ok=True)

    corr = df.corr(numeric_only=True)
    print(corr)

    plt.figure(figsize=(14, 12))
    plt.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    plt.colorbar(label="Correlation")

    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.columns)), corr.columns)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)

    plt.title("Matrice de correlation - Duree trajet")
    plt.tight_layout()

    plt.savefig(os.path.join(MATRICES_DIR, "Matrice_correlation_duree_trajet_ExtraTreesRegressor.png"), dpi=120)

    plt.savefig(os.path.join(MATRICES_DIR, "Matrice_correlation_duree_trajet_ExtraTreesRegressor.png"), dpi=150, bbox_inches="tight")
    plt.close()

    print("Matrice de corrélation crée")


# ============================================================
# 4. PREPARATION DES VARIABLES
# ============================================================

def preparation_variable(df):

    print("\n2. Preparation des variables")
    print("-" * 50)

    df["meme_zone"] = (df["id_location_depart"] == df["id_location_arrivee"]).astype(int)

    df["est_weekend"] = df["est_weekend"].astype(int)

    df["trajet_aeroport"] = (df[["sz_depart", "sz_arrivee"]].isin(["Airports", "EWR"]).any(axis=1).astype(int))

    # Encodage cyclique des 48 creneaux de 30 minutes
    df["creneau_sin"] = np.sin(2 * np.pi * df["creneau_jour"] / 48)

    df["creneau_cos"] = np.cos(2 * np.pi * df["creneau_jour"] / 48)

    print("Variables localisation et temps préparées")

# ============================================================
# 5. DECOUPAGE TEMPOREL : 80 % TRAIN / 20 % TEST
# ============================================================

def repartition_train_test(df):
    
    date_coupure = df["date_heure"].quantile(0.8)

    train = df[df["date_heure"] <= date_coupure].drop(columns="date_heure").copy()

    test = df[df["date_heure"] > date_coupure].drop(columns="date_heure").copy()


    # Encodage des variables categorielles
    colonnes_cat = ["arr_depart", "arr_arrivee", "sz_depart", "sz_arrivee"]

    train = pd.get_dummies(train, columns=colonnes_cat, dtype=int)

    test = pd.get_dummies(test, columns=colonnes_cat, dtype=int)

    # Meme colonnes et meme ordre pour train et test
    test = test.reindex(columns=train.columns, fill_value=0)


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

    
    print ("Répartition, train et test réalisé")
    return (X_train, y_train, X_test, y_test, mediane)

# ============================================================
# 6. DEFINITION DES DEUX MODELES
# ============================================================

def choix_modeles():
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
    print("Les modèles ont été choisit")

    return modeles


# ============================================================
# 7. ENTRAINEMENT ET EVALUATION
# ============================================================

def entrainement_modeles(modeles, X_train, y_train, X_test,y_test):

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

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        r2 = r2_score(y_test, y_pred)

        resultats[nom] = {
            "MAE (min)": mae,
            "RMSE (min)": rmse,
            "R2": r2
        }

        print(f"MAE  : {mae:.3f} minutes")
        print(f"RMSE : {rmse:.3f} minutes")
        print(f"R2   : {r2:.4f}")

    print("entrainement des modèles réalisé")

    return (resultats, predictions)

# ============================================================
# 8. COMPARAISON DES RESULTATS
# ============================================================
def comparaison_resulats(resultats, modeles):
        
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

    deuxieme_nom = df_classement.index[1]
    deuxieme_model = modeles[deuxieme_nom]

    print("\nMeilleur modele selon la MAE :")
    print(meilleur_nom)

    print(f"MAE  : {df_resultats.loc[meilleur_nom, 'MAE (min)']:.3f} min")
    print(f"RMSE : {df_resultats.loc[meilleur_nom, 'RMSE (min)']:.3f} min")
    print(f"R2   : {df_resultats.loc[meilleur_nom, 'R2']:.4f}")

    print("Comparaison des modèles avec le MAE, RMSE et R2")

    return (meilleur_model, meilleur_nom, deuxieme_model, deuxieme_nom, df_resultats)

# ============================================================
# 9. COMPARAISON AVEC LE MODELE NAIF
# ============================================================

def comparaison_modele_naif(y_test,y_train):
    print("\n5. Modele naif")
    print("-" * 50)

    y_naif = np.full(len(y_test), y_train.mean())

    mae_naif = mean_absolute_error(y_test, y_naif)
    rmse_naif = np.sqrt(mean_squared_error(y_test, y_naif))
    r2_naif = r2_score(y_test, y_naif)

    print(f"MAE  naive : {mae_naif:.3f} min")
    print(f"RMSE naive : {rmse_naif:.3f} min")
    print(f"R2 naive   : {r2_naif:.4f}")

    print("comparaison des modèles avec un modèle naïf exécuté")

    return (mae_naif, rmse_naif, r2_naif)

# ============================================================
# 10. IMPORTANCE DES VARIABLES DU MEILLEUR MODELE
# ============================================================

def choix_meilleur_modele(meilleur_model, meilleur_nom, X_train,):

    print("\n6. Importance des variables")
    print("-" * 50)

    importances = (pd.Series(meilleur_model.feature_importances_,index=X_train.columns).sort_values(ascending=False))

    print(f"Modele analyse : {meilleur_nom}")
    print("\nTop 10 variables :")
    print(importances.head(10).round(4))


    # Importance totale des variables de trafic selectionnees
    trafic = importances[importances.index.str.startswith(("lenteur_", "nb_lag", "nb_roll"))]

    print(f"\nImportance totale du trafic : {trafic.sum():.4f}")
    print(trafic.round(4))

    print("Le meilleur des deux modèles est choisit")


# ============================================================
# 11. GRAPHIQUE DE COMPARAISON DES MAE
# ============================================================

def creation_graphique_mae(df_resultats,mae_naif):

    plt.figure(figsize=(8, 5))

    plt.bar(df_resultats.index, df_resultats["MAE (min)"])

    plt.axhline(mae_naif, linestyle="--", label="Modele naif")

    plt.ylabel("MAE (minutes)")
    plt.title("Comparaison des modeles - Duree des trajets")
    plt.legend()
    plt.tight_layout()

    plt.savefig(os.path.join(DATA_DIR, "comparaison_modeles_duree.png"), dpi=120)

    plt.show()
    plt.close()

    print("graphique des résultats créé")


# ============================================================
# 12. SAUVEGARDE DU MEILLEUR MODELE
# ============================================================

def sauvegarde_modele_choisi(meilleur_model, meilleur_nom, X_train, mediane, df_resultats, deuxieme_model, deuxieme_nom, mae_naif):
            
    artefact = {
        "model": meilleur_model,
        "nom_modele": meilleur_nom,
        "colonnes": list(X_train.columns),
        "mediane": mediane,
        "metriques": df_resultats.loc[meilleur_nom].to_dict()
    }

    second = {
        "model": deuxieme_model,
        "nom_modele": deuxieme_nom,
        "colonnes": list(X_train.columns),
        "mediane": mediane,
        "metriques_deuxieme": df_resultats.loc[deuxieme_nom].to_dict()
    }

    joblib.dump(artefact, MODEL_PATH_1ST)
    joblib.dump(second, MODEL_PATH_2ND)

    print(f"\nMeilleur modele sauvegarde : {MODEL_PATH_1ST}")
    print(f"Modele retenu : {meilleur_nom}")

    metadonnees_1er = {
        "algorithme": type(meilleur_model).__name__,
        "nom_modele": meilleur_nom,
        "version": MODEL_VERSION,
        "date_entrainement": datetime.now().isoformat(),
        "metriques": {
            "mae_minutes": float(df_resultats.loc[meilleur_nom, "MAE (min)"]),
            "rmse_minutes": float(df_resultats.loc[meilleur_nom, "RMSE (min)"]),
            "r2": float(df_resultats.loc[meilleur_nom, "R2"]),
            "mae_naif_minutes": float(mae_naif),
        },
    }

    metadonnees_2eme = {
        "algorithme": type(deuxieme_model).__name__,
        "nom_modele": deuxieme_nom,
        "date_entrainement": datetime.now().isoformat(),
        "metriques": {
            "mae_minutes": float(df_resultats.loc[deuxieme_nom, "MAE (min)"]),
            "rmse_minutes": float(df_resultats.loc[deuxieme_nom, "RMSE (min)"]),
            "r2": float(df_resultats.loc[deuxieme_nom, "R2"]),
            "mae_naif_minutes": float(mae_naif),
        },
    }

    with open(os.path.join(EVALUATION_DIR, "rapport_entrainement_modeles.json"), "a", encoding="utf-8") as f:
        json.dump({"premier_modele" : metadonnees_1er, "deuxieme_modele" : metadonnees_2eme}, f, indent=4, ensure_ascii=False)

    print ("modèle sauvegardé et rapports réalisés")

# ============================================================
# EXECUTION
# ============================================================
def main_train():

# Etape 1 : Définition des features
    df = extraction_donnees()
    print ("Etape 1/11 terminé : définition des features")

# Etape 2 : Création d'une matrice de corrélation
    creation_matrice(df)
    print ("Etape 2/11 terminé : Création et sauvegarde de la matrice de corrélation")

# Etape 3 : Préparation des variables de localisation et de temps
    preparation_variable(df)
    print ("Etape 3/11 terminé : Transfromation des données de localisation et de temps")

# Etape 4 : Répartition des données pour l'entrainement et le test
    repartition = repartition_train_test(df)
    print ("Etape 4/11 terminé : Répartition des données pour l'entrainement et le test pour les ML")

# Etape 5 : Choix des modèles ML
    model = choix_modeles()
    print ("Etape 5/11 terminé : Choix des modèles ML pour une futur comparaison")

# Etape 6 : Entrainement des deux modèles ML choisis
    entrainement = entrainement_modeles(model, repartition[0], repartition[1], repartition[2], repartition[3])
    print ("Etape 6/11 terminé : Entrainement des deux modèles ML choisis")

# Etape 7 : Comparaison des résultats des ML
    res = comparaison_resulats(entrainement[0],model)
    print ("Etape 7/11 terminé : Comparaison des deux modèles ML sur leurs résultats")

# Etape 8 : Comparaison des ML avec un modele naïf
    res_comparaison_model = comparaison_modele_naif(repartition[3],repartition[1])
    print ("Etape 8/11 terminé : Comparaison des résultats des ML avec un modèle naïf")

# Etape 9 : Choix du meilleur des deux modèles
    choix_meilleur_modele(res[0], res[1], repartition[0])
    print ("Etape 9/11 terminé : Sélectionné le meilleur des deux ML")

# Etape 10 : Création d'un graphique sur le MAE
    # Etape 10 : Création d'un graphique sur la MAE
    creation_graphique_mae(res[4], res_comparaison_model[0])
    print ("Etape 10/11 terminé : Création du graphique de la MAE")
    
# Etape 11 : Sauvegarde du modèle et création d'un rapport pour les archives
    sauvegarde_modele_choisi(res[0], res[1], repartition[0], repartition[4], res[4], res[2], res[3],res_comparaison_model[0])
    print ("Etape 11/11 terminé : Sauvegarde du modèle retenu et création d'un rapport pour les archives")
    print ("Pipeline train_model_extra_trees_regressor.py terminé")
