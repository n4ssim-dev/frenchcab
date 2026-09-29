import pandas as pd
from pathlib import Path
import duckdb

CSV_PATH = "ms_api_metier/data/raw/yellow_tripdata_2026-07.csv"
OUTPUT_PATH = "ms_api_metier/data/yellow_tripdata_2026-07_propre.csv"
dossier_sortie = Path("ms_api_metier/data/lignes_rejetees")
dossier_sortie.mkdir(parents=True, exist_ok=True)
REJETS_PATH = "yellow_taxi_lignes_rejetees.csv"
SQL_DB = "ms_api_metier/data/yellow_taxi.db"
ZONES_PATH = "ms_api_metier/data/raw/taxi_zone_lookup.csv"


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

    # Date dans le futur
    maintenant = pd.Timestamp.now()
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


    df_rejets_total = pd.concat([df_rejets_doublons, df_rejets_date_manquante, df_rejets_date_manquante2, df_rejets_date_futur,df_rejets_date_futur2, df_rejets_date_futur], ignore_index=True)
    df_rejets_total.to_csv(dossier_sortie / REJETS_PATH, index=False)

    
    valeurs_manquantes = df.isnull().sum().sum()
    print(f"\nTotal valeurs manquantes : {valeurs_manquantes}\n")
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nFichier nettoyé : '{OUTPUT_PATH}'")
    print(f"\nFichier lignes rejetées généré : '{REJETS_PATH}'")

    return df


def creer_db ():

    con = duckdb.connect(SQL_DB)
    con.execute("""
        CREATE OR REPLACE TABLE taxi_zones (
            LocationID   INTEGER PRIMARY KEY,
            Borough      VARCHAR,
            Zone         VARCHAR,
            service_zone VARCHAR
        )
    """)
    con.execute(f"""
        INSERT INTO taxi_zones
        SELECT * FROM read_csv_auto('{Path(ZONES_PATH).as_posix()}', header=true)
    """)

    
    con.execute("""
        CREATE OR REPLACE TABLE yellowtripdata (
            VendorID              INTEGER,
            tpep_pickup_datetime  TIMESTAMP,
            tpep_dropoff_datetime TIMESTAMP,
            passenger_count       DOUBLE,
            trip_distance         DOUBLE,
            PULocationID          INTEGER REFERENCES taxi_zones(LocationID),
            DOLocationID          INTEGER REFERENCES taxi_zones(LocationID),
            total_amount          DOUBLE
            
        )
    """)

    con.execute(f"""
        INSERT INTO yellowtripdata
        SELECT VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
               passenger_count, trip_distance, PULocationID, DOLocationID, total_amount
        FROM read_csv_auto('{Path(OUTPUT_PATH).as_posix()}', header=true)
    """)
    # 

    # con.execute(f"""
    # CREATE OR REPLACE TABLE yellowtripdata AS
    # SELECT *
    # FROM read_csv_auto(
    #     '{Path(OUTPUT_PATH).as_posix()}',
    #     header=true
    # )
    # """)
    # # Vérification
    # nb = con.execute("SELECT COUNT(*) FROM yellowtripdata").fetchone()[0]
    # print(f"\n{nb} lignes importées lors de la génération de la base.")



def main():
    df = lire_csv()
    df = nettoyage_csv(df)
    creer_db ()
    
    
if __name__ == "__main__":
    main()
