import sqlite3

import pytest

import load

# ---------------------------------------------------------------------------
# Fausses données : un mini CSV de zones et un mini CSV de trajets.
# On ne teste JAMAIS sur la vraie base (3,5 millions de lignes = trop lent,
# et on risquerait de l'abîmer). On travaille dans tmp_path, un dossier
# temporaire que pytest crée puis efface tout seul.
# ---------------------------------------------------------------------------
ZONES = """"LocationID","Borough","Zone","service_zone"
1,"EWR","Newark Airport","EWR"
2,"Queens","Jamaica Bay","Boro Zone"
3,"Manhattan","Midtown","Yellow Zone"
264,"Unknown","N/A","N/A"
"""

COLONNES = ("VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,"
            "trip_distance,RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,"
            "payment_type,fare_amount,extra,mta_tax,tip_amount,tolls_amount,"
            "improvement_surcharge,total_amount,congestion_surcharge,Airport_fee,"
            "cbd_congestion_fee,request_source")

TRAJETS = COLONNES + """
1,2026-07-01 10:00:00,2026-07-01 10:30:00,2.0,5.0,1.0,N,1,2,1,20.0,1.0,0.5,3.0,0.0,1.0,25.5,2.5,0.0,0.0,
2,2026-07-02 18:15:00,2026-07-02 18:25:00,,1.2,,Y,2,3,2,8.0,0.0,0.5,0.0,0.0,1.0,9.5,,,0.75,app
1,2026-07-03 08:00:00,2026-07-03 08:45:00,1.0,12.0,1.0,N,3,1,1,45.0,0.0,0.5,9.0,6.0,1.0,61.5,2.5,1.75,0.0,
2,2026-07-04 23:00:00,2026-07-04 23:20:00,1.0,4.0,1.0,N,2,999,1,15.0,0.0,0.5,2.0,0.0,1.0,18.5,0.0,0.0,0.0,
"""
# Ligne 2 : cases vides (passenger_count, RatecodeID, Airport_fee...) + flag 'Y'
# Ligne 4 : zone 999 qui n'existe pas -> doit être retirée


@pytest.fixture
def fausse_base(tmp_path, monkeypatch):
    """Redirige load.py vers des fichiers temporaires."""
    zones = tmp_path / "zones.csv"
    trajets = tmp_path / "trajets.csv"
    zones.write_text(ZONES, encoding="utf-8")
    trajets.write_text(TRAJETS, encoding="utf-8")

    # monkeypatch remplace une variable du module PENDANT le test seulement
    monkeypatch.setattr(load, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(load, "ZONES_CSV", zones)
    monkeypatch.setattr(load, "TRAJETS_CSV", trajets)
    monkeypatch.setattr(load, "NB_TRAJETS_AVEC_CLIENT", 2)

    load.creer_base_si_inexistante()
    return load.DB_PATH


@pytest.fixture
def base_remplie(fausse_base):
    load.importer_donnees()
    conn = sqlite3.connect(fausse_base)
    yield conn
    conn.close()


def compter(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ---------------------------------------------------------------------------
# 1. Création des tables
# ---------------------------------------------------------------------------
def test_creerBase_creeLes4Tables(fausse_base):
    conn = sqlite3.connect(fausse_base)
    tables = {t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"clients", "lieux", "reservations", "trajets"} <= tables


def test_creerBase_deuxFoisSansErreur(fausse_base, capsys):
    load.creer_base_si_inexistante()  # 2e appel : ne doit pas planter
    assert "existe déjà" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 2. Mot de passe
# ---------------------------------------------------------------------------
def test_hacher_neStockePasEnClair():
    h = load.hacher("Alice2026!")
    assert h != "Alice2026!"
    assert len(h) == 64                      # sha256 = 64 caractères hexadécimaux
    assert h == load.hacher("Alice2026!")    # même entrée -> même empreinte


# ---------------------------------------------------------------------------
# 3. Import complet
# ---------------------------------------------------------------------------
def test_nombreDeLignes(base_remplie):
    assert compter(base_remplie, "lieux") == 4
    assert compter(base_remplie, "clients") == len(load.CLIENTS_EXEMPLE)
    assert compter(base_remplie, "trajets") == 3          # la ligne zone 999 est retirée
    assert compter(base_remplie, "reservations") == 2     # NB_TRAJETS_AVEC_CLIENT = 2


def test_lieux_NAgardeCommeTexte(base_remplie):
    zone = base_remplie.execute("SELECT zone FROM lieux WHERE locationID = 264").fetchone()[0]
    assert zone == "N/A"


def test_trajets_conversions(base_remplie):
    flag, passagers, ratecode, airport = base_remplie.execute("""
        SELECT store_and_fwd_flag, passenger_count, RateCodeID, airport_fee
        FROM trajets WHERE tpep_pickup_datetime = '2026-07-02 18:15:00'
    """).fetchone()
    assert flag == 1          # 'Y' -> 1
    assert passagers == 1     # vide -> 1
    assert ratecode == 99     # vide -> 99
    assert airport == 0.0     # vide -> 0


def test_trajets_colonnesCalculees(base_remplie):
    duree, heure, jour = base_remplie.execute("""
        SELECT trip_duration_min, pickup_hour, pickup_weekday
        FROM trajets WHERE tpep_pickup_datetime = '2026-07-01 10:00:00'
    """).fetchone()
    assert duree == 30.0
    assert heure == 10
    assert jour == 2          # 01/07/2026 = mercredi (0 = lundi)


def test_clesEtrangeres_ok(base_remplie):
    # PRAGMA foreign_key_check renvoie la liste des liens cassés : doit être vide
    assert base_remplie.execute("PRAGMA foreign_key_check").fetchall() == []


def test_reservations_lieesAuxTrajets(base_remplie):
    nb = base_remplie.execute("""
        SELECT COUNT(*) FROM trajets t
        JOIN reservations r ON r.uid_reservation = t.uid_reservation
        JOIN clients c      ON c.uid_client      = r.uid_client
        WHERE r.resa_PU_locationID = t.PU_locationID
    """).fetchone()[0]
    assert nb == 2


def test_relancer_pasDeDoublons(base_remplie, fausse_base):
    load.importer_donnees()   # 2e import
    assert compter(base_remplie, "clients") == len(load.CLIENTS_EXEMPLE)
    assert compter(base_remplie, "trajets") == 3