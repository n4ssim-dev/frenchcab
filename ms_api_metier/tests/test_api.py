from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_telechargementOk(tmp_path):
    fichier = tmp_path / "yellow_tripdata_2026-05.parquet"

    with patch("routes.donnees.downloadData", return_value=fichier) as mock_dl:
        response = client.post("/donnees/telechargement", params={"mois": "2026-07"})

    mock_dl.assert_called_once_with(mois="2026-07")
    assert response.status_code == 201
    assert response.json() == {"mois": "2026-07", "parquet": fichier.name}


def test_telechargementIndisponible():
    with patch("routes.donnees.downloadData", return_value=None):
        response = client.post("/donnees/telechargement", params={"mois": "2026-07"})

    assert response.status_code == 502


def test_moisInvalide():
    response = client.post("/donnees/telechargement", params={"mois": "2026-13"})

    assert response.status_code == 422


def test_zonesOk(tmp_path):
    fichier = tmp_path / "taxi_zone_lookup.csv"

    with patch("routes.donnees.downloadData2", return_value=fichier):
        response = client.post("/donnees/zones")

    assert response.status_code == 201
    assert response.json() == {"zones": fichier.name}


def test_zonesIndisponible():
    with patch("routes.donnees.downloadData2", return_value=None):
        response = client.post("/donnees/zones")

    assert response.status_code == 502


def test_etlFichiersManquants(tmp_path):
    with patch("routes.donnees.RAW_DIR", tmp_path):
        response = client.post("/donnees/etl", params={"mois": "2026-07"})

    assert response.status_code == 404
    assert "yellow_tripdata_2026-07.csv" in response.json()["detail"]


def test_etlOk(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "taxi_zone_lookup.csv").write_text(
        "LocationID,Borough,Zone,service_zone\n1,EWR,Newark Airport,EWR\n2,Queens,Jamaica Bay,Boro Zone\n"
    )
    entete = (
    "VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance,"
    "RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,payment_type,fare_amount,"
    "extra,mta_tax,tip_amount,tolls_amount,improvement_surcharge,total_amount,"
    "congestion_surcharge,Airport_fee,cbd_congestion_fee\n"
)
    ligne = "1,2026-07-01 10:00:00,2026-07-01 10:20:00,1.0,3.5,1.0,N,1,2,1,15.0,1.0,0.5,3.0,0.0,1.0,23.0,2.5,0.0,0.0"
    ligne_future = "2,2099-01-01 10:00:00,2099-01-01 10:20:00,1.0,2.0,1.0,N,2,1,1,10.0,0.0,0.5,0.0,0.0,1.0,11.5,2.5,0.0,0.0"
    
    (raw / "yellow_tripdata_2026-07.csv").write_text(
        entete + f"{ligne}\n{ligne}\n{ligne_future}\n"
    )

    with patch("routes.donnees.RAW_DIR", raw), patch("routes.donnees.DATA_DIR", tmp_path):
        response = client.post("/donnees/etl", params={"mois": "2026-07"})

    assert response.status_code == 201
    assert response.json()["lignes_propres"] == 1
    assert (tmp_path / "yellow_tripdata_2026-07_propre.csv").exists()
    assert (tmp_path / "lignes_rejetees" / "yellow_taxi_lignes_rejetees_2026-07.csv").exists()
    assert (tmp_path / "yellow_taxi.db").exists()
