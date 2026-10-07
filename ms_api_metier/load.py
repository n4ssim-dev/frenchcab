import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR/ "data" / "frenchcab.db"
TRAJETS_CSV = DATA_DIR / "yellow_tripdata_2026-07_propre.csv"
ZONES_CSV = DATA_DIR / "raw" / "taxi_zone_lookup.csv"



def creer_base_si_inexistante():
    base_existe = DB_PATH.exists()

    conn = sqlite3.connect(DB_PATH)

    # activer les clés étrangères
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    #  clients

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            uid_client INTEGER PRIMARY KEY,
            nom VARCHAR(30) NOT NULL,
            email VARCHAR(30) NOT NULL,
            password VARCHAR(30) NOT NULL
        )
    """)

    #  lieux

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lieux (
            locationID INTEGER PRIMARY KEY,
            borough VARCHAR(30) NOT NULL,
            zone VARCHAR(30) NOT NULL,
            service_zone VARCHAR(30) NOT NULL
        )
    """)

    #  reservations

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            uid_reservation INTEGER PRIMARY KEY,
            resa_PU_locationID INTEGER NOT NULL,
            resa_DO_locationID INTEGER NOT NULL,
            resa_date DATE NOT NULL,
            resa_heure TIME NOT NULL,
            estimation_duree_course REAL NOT NULL,
            date_heure_reservation DATETIME NOT NULL,
            statut_resa INTEGER NOT NULL,
            uid_client INTEGER NOT NULL,

            FOREIGN KEY (uid_client)
                REFERENCES clients(uid_client),

            FOREIGN KEY (resa_PU_locationID)
                REFERENCES lieux(locationID),

            FOREIGN KEY (resa_DO_locationID)
                REFERENCES lieux(locationID)
        )
    """)

    #  trajets

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trajets (
            uid_trajet INTEGER PRIMARY KEY,
            VendorID INTEGER NOT NULL,
            tpep_pickup_datetime DATETIME NOT NULL,
            tpep_dropoff_datetime DATETIME NOT NULL,
            PU_locationID INTEGER NOT NULL,
            DO_locationID INTEGER NOT NULL,
            passenger_count INTEGER NOT NULL,
            trip_distance REAL NOT NULL,
            RateCodeID INTEGER NOT NULL,
            store_and_fwd_flag INTEGER NOT NULL,
            payment_type INTEGER NOT NULL,
            fare_amount REAL NOT NULL,
            extra REAL,
            mta_tax REAL,
            tip_amount REAL,
            tolls_amount REAL,
            improvement_surcharge REAL,
            total_amount REAL NOT NULL,
            congestion_surcharge REAL,
            airport_fee REAL NOT NULL,
            cbd_congestion_fee REAL,
            trip_duration_min REAL NOT NULL,
            pickup_hour INTEGER,
            pickup_weekday INTEGER,
            uid_reservation INTEGER UNIQUE,

            FOREIGN KEY (PU_locationID)
                REFERENCES lieux(locationID),

            FOREIGN KEY (DO_locationID)
                REFERENCES lieux(locationID),

            FOREIGN KEY (uid_reservation)
                REFERENCES reservations(uid_reservation)
        )
    """)

    conn.commit()
    conn.close()

    if base_existe:
        print("La base de données existe déjà.")
    else:
        print(f"Base de données créée : {DB_PATH}")



#import

# --- paramètres --------------------------------------------------------------
NB_TRAJETS_AVEC_CLIENT = 50_000
GRAINE = 42

# statut
# 0 = en attente,
# 1 = confirmée,
# 2 = terminée,
# 3 = annulée
STATUT_TERMINEE = 2

# client
# Le "poids" = la fréquence d'utilisation un client de poids 10 fait
# environ 10 fois plus de trajets qu'un client de poids 1

CLIENTS_EXEMPLE = [
    ("Alice Martin",     "alice.martin@mail.fr",   "Alice2026!",  10),  # grosse utilisatrice
    ("Bruno Lefevre",    "bruno.lefevre@mail.fr",  "Bruno2026!",   8),
    ("Chloe Bernard",    "chloe.bernard@mail.fr",  "Chloe2026!",   6),
    ("David Moreau",     "david.moreau@mail.fr",   "David2026!",   5),
    ("Emma Laurent",     "emma.laurent@mail.fr",   "Emma2026!",    5),
    ("Farid Benali",     "farid.benali@mail.fr",   "Farid2026!",   4),
    ("Gaelle Simon",     "gaelle.simon@mail.fr",   "Gaelle2026!",  4),
    ("Hugo Michel",      "hugo.michel@mail.fr",    "Hugo2026!",    3),
    ("Ines Garcia",      "ines.garcia@mail.fr",    "Ines2026!",    3),
    ("Julien Roux",      "julien.roux@mail.fr",    "Julien2026!",  2),
    ("Karima Haddad",    "karima.haddad@mail.fr",  "Karima2026!",  2),
    ("Lucas Fournier",   "lucas.fournier@mail.fr", "Lucas2026!",   2),
    ("Manon Girard",     "manon.girard@mail.fr",   "Manon2026!",   1),
    ("Nathan Dupont",    "nathan.dupont@mail.fr",  "Nathan2026!",  1),
    ("Oceane Petit",     "oceane.petit@mail.fr",   "Oceane2026!",  1),  # cliente occasionnelle
]


def hacher(mot_de_passe):

    # mot de passes hash
    return hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()


#vider les tables (opour dublons doublons)
def vider_tables(conn):

    for table in ("trajets", "reservations", "clients", "lieux"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    print("Tables vidées.")


# lieux
def importer_lieux(conn):

    zones = pd.read_csv(ZONES_CSV, keep_default_na=False)
    zones = zones.rename(columns={
        "LocationID": "locationID",
        "Borough": "borough",
        "Zone": "zone",
    })
    for col in ("borough", "zone", "service_zone"):
        zones[col] = zones[col].replace("", "Inconnu")

    zones[["locationID", "borough", "zone", "service_zone"]].to_sql(
        "lieux", conn, if_exists="append", index=False
    )
    print(f"lieux        : {len(zones)} lignes")
    return set(zones["locationID"])


# clients
def importer_clients(conn):
    lignes = [
        (i, nom, email, hacher(mdp))
        for i, (nom, email, mdp, _poids) in enumerate(CLIENTS_EXEMPLE, start=1)
    ]
    conn.executemany(
        "INSERT INTO clients (uid_client, nom, email, password) VALUES (?, ?, ?, ?)",
        lignes,
    )
    conn.commit()
    print(f"clients      : {len(lignes)} lignes")


# lecture / préparation des trajets
def preparer_trajets(ids_lieux):
    print("Lecture du CSV (peut prendre 1 minute)...")
    df = pd.read_csv(TRAJETS_CSV, low_memory=False)

    #renommer les colonnes du CSV -> noms des colonnes de la table
    df = df.rename(columns={
        "PULocationID": "PU_locationID",
        "DOLocationID": "DO_locationID",
        "RatecodeID": "RateCodeID",
        "Airport_fee": "airport_fee",
    })

    # dates
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])

    # col. calculées
    duree = df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    df["trip_duration_min"] = (duree.dt.total_seconds() / 60).round(2)
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
    df["pickup_weekday"] = df["tpep_pickup_datetime"].dt.dayofweek  # 0 = lundi

    # col. not nul -> valeur par défaut
    df["passenger_count"] = df["passenger_count"].fillna(1).astype(int)
    df["RateCodeID"] = df["RateCodeID"].fillna(99).astype(int)   # 99 = inconnu
    df["airport_fee"] = df["airport_fee"].fillna(0.0)
    df["congestion_surcharge"] = df["congestion_surcharge"].fillna(0.0)
    # 'Y'/'N' -> 1/0 data integer
    df["store_and_fwd_flag"] = (df["store_and_fwd_flag"] == "Y").astype(int)


    avant = len(df)
    df = df[df["PU_locationID"].isin(ids_lieux) & df["DO_locationID"].isin(ids_lieux)]
    print(f"Trajets avec zone inconnue retirés : {avant - len(df)}")

    df = df.reset_index(drop=True)
    return df


#réservations (trajet <-> client)

def creer_reservations(conn, df):
    rng = np.random.default_rng(GRAINE)
    n = min(NB_TRAJETS_AVEC_CLIENT, len(df))

    # tirer les trajets qui auront un client
    index_choisis = rng.choice(len(df), size=n, replace=False)
    choisis = df.loc[index_choisis]

    #choisir un client pour chaque trajet, selon les poids
    poids = np.array([c[3] for c in CLIENTS_EXEMPLE], dtype=float)
    uid_clients = rng.choice(np.arange(1, len(CLIENTS_EXEMPLE) + 1), size=n, p=poids / poids.sum())

    #client a réservé entre 10 min et 2 h avant le départ
    avance = pd.to_timedelta(rng.integers(10, 121, size=n), unit="m")

    resa = pd.DataFrame({
        "uid_reservation": np.arange(1, n + 1),
        "resa_PU_locationID": choisis["PU_locationID"].values,
        "resa_DO_locationID": choisis["DO_locationID"].values,
        "resa_date": choisis["tpep_pickup_datetime"].dt.strftime("%Y-%m-%d").values,
        "resa_heure": choisis["tpep_pickup_datetime"].dt.strftime("%H:%M:%S").values,
        "estimation_duree_course": choisis["trip_duration_min"].values,
        "date_heure_reservation": (choisis["tpep_pickup_datetime"] - avance.values)
                                  .dt.strftime("%Y-%m-%d %H:%M:%S").values,
        "statut_resa": STATUT_TERMINEE,
        "uid_client": uid_clients,
    })
    resa.to_sql("reservations", conn, if_exists="append", index=False, chunksize=10_000)
    print(f"reservations : {len(resa)} lignes")

    # écrire l'uid_reservation dans les trajets choisis
    df["uid_reservation"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[index_choisis, "uid_reservation"] = resa["uid_reservation"].values
    return df


# trajets
COLONNES_TRAJETS = [
    "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "PU_locationID", "DO_locationID", "passenger_count", "trip_distance",
    "RateCodeID", "store_and_fwd_flag", "payment_type", "fare_amount", "extra",
    "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "total_amount", "congestion_surcharge", "airport_fee", "cbd_congestion_fee",
    "trip_duration_min", "pickup_hour", "pickup_weekday", "uid_reservation",
]


def importer_trajets(conn, df):

    for col in ("tpep_pickup_datetime", "tpep_dropoff_datetime"):
        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    print("Insertion des trajets (quelques minutes)...")
    df[COLONNES_TRAJETS].to_sql(
        "trajets", conn, if_exists="append", index=False, chunksize=50_000
    )
    print(f"trajets      : {len(df)} lignes")



def importer_donnees():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    vider_tables(conn)
    ids_lieux = importer_lieux(conn)
    importer_clients(conn)
    df = preparer_trajets(ids_lieux)
    df = creer_reservations(conn, df)
    importer_trajets(conn, df)

    conn.commit()
    conn.close()
    print(f"\nTerminé ! Base : {DB_PATH}")


if __name__ == "__main__":
    creer_base_si_inexistante()
    importer_donnees()