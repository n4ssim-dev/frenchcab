import pandas as pd
from pathlib import Path
import duckdb

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CSV_PATH = "data/raw/yellow_tripdata_2026-07.csv"
OUTPUT_PATH = "data/yellow_tripdata_2026-07_propre.csv"
dossier_sortie = Path("data/lignes_rejetees")
dossier_sortie.mkdir(parents=True, exist_ok=True)
REJETS_PATH = "yellow_taxi_lignes_rejetees.csv"
SQL_DB = DATA_DIR / "yellow_taxi.db"
ZONES_CSV = DATA_DIR / "raw" / "taxi_zone_lookup.csv"


def lire_csv():
    df = pd.read_csv(CSV_PATH)
    return df

def nettoyage_csv(df):

    print("\n1 : Vérification dtypes et non-null")
    print("-" * 40)
    df.info()


    print("\n2 : Vérification si valeurs manquantes")
    print("-" * 40)
    print(df.isnull().sum())
    valeurs_manquantes = df.isnull().sum().sum()
    print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")

    print("\n3 : Modification format et coherence date")
    print("-" * 40)
       
    
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
        
    # Dates manquantes ou invalides (NaT après conversion)
    idx_manquantes = df[df["tpep_pickup_datetime"].isna()].index
    manquantes = df["tpep_pickup_datetime"].isna()
    df_rejets_date_manquante = df[manquantes].copy()
    df_rejets_date_manquante["motif_rejet"] = "date manquante"
    print(len(idx_manquantes), "ligne(s) date manquante(s) supprimée(s)")
    df = df.drop(index=idx_manquantes)

    idx_manquantes2 = df[df["tpep_dropoff_datetime"].isna()].index
    manquantes2 = df["tpep_dropoff_datetime"].isna()
    df_rejets_date_manquante2 = df[manquantes2].copy()
    df_rejets_date_manquante2["motif_rejet"] = "date manquante"
    print(len(idx_manquantes2), "ligne(s) date manquante(s) supprimée(s)")
    df = df.drop(index=idx_manquantes2)

    # Date dans le futur (apres31/07/2026)
    maintenant = "2026-07-31 23:59:59"
    futures = df[df["tpep_pickup_datetime"] > maintenant].index
    futur_rejet = df["tpep_pickup_datetime"] > maintenant
    df_rejets_date_futur = df[futur_rejet].copy()
    df_rejets_date_futur["motif_rejet"] = "date dans le futur"
    print(len(futures), "lignes date futur")
    df = df.drop(index=futures)

    futures2 = df[df["tpep_dropoff_datetime"] > maintenant].index
    futur_rejet2 = df["tpep_dropoff_datetime"] > maintenant
    df_rejets_date_futur2 = df[futur_rejet2].copy()
    df_rejets_date_futur2["motif_rejet"] = "date dans le futur"
    print(len(futures2), "lignes date futur")
    df = df.drop(index=futures2)

    # Date avant 07/2026 le passé
    date_depart = "2026-07-01 00:00:00"
    passe = df[df["tpep_pickup_datetime"] < date_depart].index
    passe_rejet = df["tpep_pickup_datetime"] < date_depart
    df_rejets_date_passe = df[passe_rejet].copy()
    df_rejets_date_passe["motif_rejet"] = "date dans le passé"
    print(len(passe), "lignes date passé")
    df = df.drop(index=passe)

    passe2 = df[df["tpep_dropoff_datetime"] < date_depart].index
    passe_rejet2 = df["tpep_dropoff_datetime"] < date_depart
    df_rejets_date_passe2 = df[passe_rejet2].copy()
    df_rejets_date_passe2["motif_rejet"] = "date dans le passé"
    print(len(passe2), "lignes date passé")
    df = df.drop(index=passe2)

    print("\n4 : Vérification et suppression doublons")
    print("-" * 40)
    nb_lignes_avant = len(df)
    print(f"\nNombre de données : {nb_lignes_avant}")
    doublons_count = df.duplicated().sum()
    print(f"\nNombre de doublons : {doublons_count}")
    doublons = df.duplicated
    df_rejets_doublons = df[doublons].copy()
    df_rejets_doublons["motif_rejet"] = "doublon"
    if doublons_count > 0:
        df = df.drop_duplicates()
        nb_lignes_apres = len(df)
        print(f"\nDoublons supprimés, nouveau nombre de données : {nb_lignes_apres}\n")
    else : 
        nb_lignes_apres = len(df)


    print("\n5 : Suppression distances incohérentes")
    print("-" * 40)
    nb_lignes_avant = len(df)
    print(f"\nNombre de données : {nb_lignes_avant}")
    distance = df["trip_distance"] > 320
    df_rejets_distance = df[distance].copy()
    df_rejets_distance["motif_rejet"] = "distance incohérente"
    df = df[df["trip_distance"] <= 320]
    print(f"\nNombre de lignes supprimées : {nb_lignes_avant - len(df)}")


    print("\n6 : Suppression durées incohérentes")
    print("-" * 40)
    nb_lignes_avant = len(df)
    print(f"\nNombre de données : {nb_lignes_avant}")
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    duree = df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    delta_duree = duree > pd.Timedelta(hours=7)
    df_rejets_duree = df[delta_duree].copy()            
    df_rejets_duree["motif_rejet"] = "durée incohérente"
    df = df[~delta_duree].copy()              
    print(f"\nNombre de lignes supprimées : {nb_lignes_avant - len(df)}")

    
    print("\n7 : Suppression paiements incohérents")
    print("-" * 40)
    nb_lignes_avant = len(df)
    print(f"\nNombre de données : {nb_lignes_avant}")
    paiement = (df["total_amount"] > 1000) & (df["trip_distance"] < 80)
    df_rejets_paiement = df[paiement].copy()
    df_rejets_paiement["motif_rejet"] = "paiement incohérent"
    df = df[~paiement]
    print(f"\nNombre de lignes supprimées : {nb_lignes_avant - len(df)}")
    

    df_rejets_total = pd.concat([df_rejets_doublons, df_rejets_date_passe, df_rejets_date_passe2, df_rejets_distance, df_rejets_paiement, df_rejets_duree, df_rejets_date_manquante, df_rejets_date_manquante2, df_rejets_date_futur,df_rejets_date_futur2], ignore_index=True)
    df_rejets_total.to_csv(dossier_sortie / REJETS_PATH, index=False)

    
    valeurs_manquantes = df.isnull().sum().sum()
    print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nFichier nettoyé : '{OUTPUT_PATH}'")
    print(f"\nFichier lignes rejetées généré : '{REJETS_PATH}'")

    return df


def creer_db(db_path=SQL_DB, zones_csv=ZONES_CSV, trajets_csv=None):

    for nom, chemin in [("zones", zones_csv), ("trajets", trajets_csv)]:
        if chemin is None or not Path(chemin).exists():
            raise FileNotFoundError(f"Fichier {nom} introuvable : {chemin}")
    zones = Path(zones_csv).as_posix()
    trajets = Path(trajets_csv).as_posix()
    con = duckdb.connect(str(db_path))

    con.execute("DROP TABLE IF EXISTS fait_trajets")
    con.execute("DROP TABLE IF EXISTS dim_temps")
    con.execute("DROP TABLE IF EXISTS dim_location")

    con.execute(f"""
CREATE OR REPLACE TEMP VIEW trajets_src AS
SELECT * REPLACE (
    CAST(tpep_pickup_datetime  AS TIMESTAMP) AS tpep_pickup_datetime,
    CAST(tpep_dropoff_datetime AS TIMESTAMP) AS tpep_dropoff_datetime
)
FROM read_csv_auto('{trajets}')
""")

#Dim_location
    con.execute("""
    CREATE TABLE dim_location (
        id_location    INTEGER PRIMARY KEY,
        arrondissement VARCHAR,
        zone           VARCHAR,
        zone_service   VARCHAR
    )
    """)
    con.execute(f"""
    INSERT INTO dim_location
    SELECT LocationID,
           COALESCE(Borough, 'Inconnu'),
           COALESCE(Zone, 'Inconnu'),
           COALESCE(service_zone, 'Inconnu')
    FROM read_csv_auto('{zones}')
    """)

#Dim temps


    con.execute("""
    CREATE TABLE dim_temps (
        id_temps        BIGINT PRIMARY KEY,   -- AAAAMMJJHHMM
        date_heure      TIMESTAMP,
        date            DATE,
        annee           INTEGER,
        trimestre       INTEGER,
        mois            INTEGER,
        jour            INTEGER,
        heure           INTEGER,
        minute          INTEGER,
        creneau_jour    INTEGER,              -- 0 à 47
        jour_semaine    INTEGER,              -- 1 = lundi
        nom_jour        VARCHAR,
        est_weekend     BOOLEAN,
        tranche_horaire VARCHAR
    )
    """)
    con.execute(f"""
    INSERT INTO dim_temps
    WITH bornes AS (
        SELECT time_bucket(INTERVAL 30 MINUTE, MIN(tpep_pickup_datetime)) AS d0,
               time_bucket(INTERVAL 30 MINUTE, MAX(tpep_pickup_datetime)) + INTERVAL 1 DAY AS d1
        FROM read_csv_auto('{OUTPUT_PATH}')
        WHERE tpep_pickup_datetime >= '2026-07-01' AND tpep_pickup_datetime < '2026-08-01'
    ),
    creneaux AS (
        SELECT unnest(generate_series(d0, d1, INTERVAL 30 MINUTE)) AS dh FROM bornes
    )
    SELECT
        CAST(strftime(dh, '%Y%m%d%H%M') AS BIGINT),
        dh, CAST(dh AS DATE), year(dh), quarter(dh), month(dh), day(dh),
        hour(dh), minute(dh), hour(dh) * 2 + (minute(dh) // 30),
        isodow(dh),
        CASE isodow(dh) WHEN 1 THEN 'Lundi' WHEN 2 THEN 'Mardi' WHEN 3 THEN 'Mercredi'
             WHEN 4 THEN 'Jeudi' WHEN 5 THEN 'Vendredi' WHEN 6 THEN 'Samedi'
             ELSE 'Dimanche' END,
        isodow(dh) >= 6,
        CASE WHEN hour(dh) < 6 THEN 'Nuit' WHEN hour(dh) < 12 THEN 'Matin'
             WHEN hour(dh) < 18 THEN 'Après-midi' ELSE 'Soir' END
    FROM creneaux
    ORDER BY dh
    """)


#fait trajets

    con.execute("""
CREATE TABLE fait_trajets (
    id_trajet              INTEGER PRIMARY KEY,
    id_temps_depart        BIGINT REFERENCES dim_temps(id_temps),
    id_temps_arrivee       BIGINT REFERENCES dim_temps(id_temps),
    id_location_depart     INTEGER REFERENCES dim_location(id_location),
    id_location_arrivee    INTEGER REFERENCES dim_location(id_location),
    id_vendeur             INTEGER,
    id_tarif               INTEGER,
    type_paiement          INTEGER,
    store_and_fwd_flag     VARCHAR,
    nb_passagers           DOUBLE,
    distance               DOUBLE,
    duree_minutes          DOUBLE,
    montant_course         DOUBLE,
    supplement             DOUBLE,
    taxe_mta               DOUBLE,
    pourboire              DOUBLE,
    peages                 DOUBLE,
    surcharge_amelioration DOUBLE,
    surcharge_congestion   DOUBLE,
    frais_aeroport         DOUBLE,
    frais_cbd              DOUBLE,
    montant_total          DOUBLE
)
""")
    con.execute(f"""
INSERT INTO fait_trajets
SELECT
    row_number() OVER (ORDER BY tpep_pickup_datetime),
    CAST(strftime(time_bucket(INTERVAL 30 MINUTE, tpep_pickup_datetime),  '%Y%m%d%H%M') AS BIGINT),
    CAST(strftime(time_bucket(INTERVAL 30 MINUTE, tpep_dropoff_datetime), '%Y%m%d%H%M') AS BIGINT),
    PULocationID,
    DOLocationID,
    VendorID,
    CAST(RatecodeID AS INTEGER),
    payment_type,
    store_and_fwd_flag,
    passenger_count,
    trip_distance,
    ROUND(date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0, 2),
    fare_amount, extra, mta_tax, tip_amount, tolls_amount,
    improvement_surcharge, congestion_surcharge, Airport_fee,
    cbd_congestion_fee, total_amount
FROM trajets_src
WHERE PULocationID IN (SELECT id_location FROM dim_location)
  AND DOLocationID IN (SELECT id_location FROM dim_location)
""")


    con.execute("DROP TABLE IF EXISTS features_creneau")
    con.execute("""
    CREATE TABLE features_creneau AS
    WITH base AS (
        SELECT t.id_temps,
               t.date_heure,
               COUNT(f.id_trajet)              AS nb,
               COALESCE(SUM(f.duree_minutes),0) AS s_duree,
               COALESCE(SUM(f.distance),0)      AS s_dist
        FROM dim_temps t
        LEFT JOIN fait_trajets f
               ON f.id_temps_depart = t.id_temps
              AND f.duree_minutes BETWEEN 1 AND 180
              AND f.distance BETWEEN 0.1 AND 80
        GROUP BY t.id_temps, t.date_heure
    ),
    pace AS (
        SELECT *, s_duree / NULLIF(s_dist, 0) AS lenteur FROM base
    )
    SELECT
        id_temps,
        date_heure,
        -- LAGS : créneaux précédents
        LAG(nb, 1)      OVER w AS nb_lag1,
        LAG(nb, 2)      OVER w AS nb_lag2,
        LAG(nb, 48)     OVER w AS nb_lag_1j,
        LAG(lenteur, 1)  OVER w AS lenteur_lag1,
        LAG(lenteur, 2)  OVER w AS lenteur_lag2,
        LAG(lenteur, 48) OVER w AS lenteur_lag_1j,
        -- ROLLINGS : fenêtres qui EXCLUENT le créneau courant (1 PRECEDING)
        SUM(s_duree) OVER (ORDER BY id_temps ROWS BETWEEN 3  PRECEDING AND 1 PRECEDING)
          / NULLIF(SUM(s_dist) OVER (ORDER BY id_temps ROWS BETWEEN 3  PRECEDING AND 1 PRECEDING), 0)
          AS lenteur_roll_1h30,
        SUM(s_duree) OVER (ORDER BY id_temps ROWS BETWEEN 6  PRECEDING AND 1 PRECEDING)
          / NULLIF(SUM(s_dist) OVER (ORDER BY id_temps ROWS BETWEEN 6  PRECEDING AND 1 PRECEDING), 0)
          AS lenteur_roll_3h,
        SUM(s_duree) OVER (ORDER BY id_temps ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING)
          / NULLIF(SUM(s_dist) OVER (ORDER BY id_temps ROWS BETWEEN 48 PRECEDING AND 1 PRECEDING), 0)
          AS lenteur_roll_24h,
        AVG(nb) OVER (ORDER BY id_temps ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS nb_roll_3h
    FROM pace
    WINDOW w AS (ORDER BY id_temps)
    """)


    con.close()

def main():
    df = lire_csv()
    df = nettoyage_csv(df)
    creer_db (trajets_csv=OUTPUT_PATH)
    
    
if __name__ == "__main__":
    main()
