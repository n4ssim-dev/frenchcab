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
    con.execute("CREATE TABLE taxi_zones (LocationID INTEGER, Borough VARCHAR, Zone VARCHAR, service_zone VARCHAR)")
    con.execute("INSERT INTO taxi_zones VALUES (1, 'EWR', 'Newark Airport', 'EWR'), (2, 'Queens', 'Jamaica Bay', 'Boro Zone')")
    con.execute("""
        CREATE TABLE yellowtripdata (
            VendorID INTEGER, tpep_pickup_datetime TIMESTAMP, tpep_dropoff_datetime TIMESTAMP,
            passenger_count DOUBLE, trip_distance DOUBLE, PULocationID INTEGER,
            DOLocationID INTEGER, total_amount DOUBLE
        )
    """)
    for i in range(5):
        con.execute(
            "INSERT INTO yellowtripdata VALUES (1, '2026-07-01 10:00:00', '2026-07-01 10:20:00', 1, ?, 1, 2, 20.5)",
            [float(i)],
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
