from unittest.mock import patch

import duckdb
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

@pytest.fixture
def base(tmp_path):
    chemin = tmp_path / "yellow_taxi.db"
    con = duckdb.connect(str(chemin))
    # Mêmes tables que celles créées par etl.py (modèle en étoile)
    con.execute("CREATE TABLE dim_location (id_location INTEGER, arrondissement VARCHAR, zone VARCHAR, zone_service VARCHAR)")
    con.execute("INSERT INTO dim_location VALUES (1, 'EWR', 'Newark Airport', 'EWR'), (2, 'Queens', 'Jamaica Bay', 'Boro Zone')")
    con.execute("CREATE TABLE dim_temps (id_temps BIGINT, date_heure TIMESTAMP, date DATE)")
    con.execute("INSERT INTO dim_temps VALUES (202607011000, '2026-07-01 10:00:00', '2026-07-01')")
    con.execute("""
        CREATE TABLE fait_trajets (
            id_trajet INTEGER, id_temps_depart BIGINT, id_temps_arrivee BIGINT,
            id_location_depart INTEGER, id_location_arrivee INTEGER, id_vendeur INTEGER,
            id_tarif INTEGER, type_paiement INTEGER, store_and_fwd_flag VARCHAR,
            nb_passagers DOUBLE, distance DOUBLE, duree_minutes DOUBLE,
            pourboire DOUBLE, peages DOUBLE, montant_total DOUBLE
        )
    """)
    for i in range(5):
        con.execute(
            "INSERT INTO fait_trajets VALUES (?, 202607011000, 202607011000, 1, 2, 1, 1, 1, 'N', 1, ?, 20, 0, 0, 20.5)",
            [i, float(i)],
        )
    con.close()

    with patch("routes.courses.DB_PATH", chemin):
        yield chemin

def test_listePaginee(base):
    response = client.get("/courses", params={"limit": 2, "offset": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert [c["id"] for c in data["courses"]] == [2, 3]
    assert data["courses"][0]["zone_depart"] == "Newark Airport"
    assert data["courses"][0]["zone_arrivee"] == "Jamaica Bay"


def test_listeLimiteParDefaut(base):
    data = client.get("/courses").json()

    assert data["limit"] == 100
    assert len(data["courses"]) == 5


def test_limitTropGrand(base):
    assert client.get("/courses", params={"limit": 5000}).status_code == 422


def test_detailCourse(base):
    response = client.get("/courses/3")

    assert response.status_code == 200
    assert response.json()["id"] == 3
    assert response.json()["distance"] == 3.0


def test_courseIntrouvable(base):
    assert client.get("/courses/99").status_code == 404


def test_baseAbsente(tmp_path):
    with patch("routes.courses.DB_PATH", tmp_path / "absente.db"):
        assert client.get("/courses").status_code == 503
