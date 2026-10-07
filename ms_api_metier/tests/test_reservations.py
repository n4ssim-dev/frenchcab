import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import load
from main import app

client = TestClient(app)

# Une réservation valide (date dans le futur)
RESA = {
    "uid_client": 1,
    "resa_PU_locationID": 1,
    "resa_DO_locationID": 2,
    "resa_date": "2099-12-01",
    "resa_heure": "14:30",
    "estimation_duree_course": 25,
}


@pytest.fixture
def base(tmp_path, monkeypatch):
    chemin = tmp_path / "frenchcab.db"
    monkeypatch.setattr(load, "DB_PATH", chemin)
    load.creer_base_si_inexistante()

    conn = sqlite3.connect(chemin)
    conn.execute("INSERT INTO clients VALUES (1, 'Alice', 'a@mail.fr', 'x')")
    conn.executemany("INSERT INTO lieux VALUES (?, 'Queens', 'Zone', 'Boro Zone')", [(1,), (2,)])
    conn.commit()
    conn.close()

    with patch("routes.reservations.DB_PATH", chemin):
        yield chemin


def test_ajouter_ok(base):
    r = client.post("/reservations", json=RESA)
    assert r.status_code == 201
    data = r.json()
    assert data["uid_reservation"] == 1
    assert data["statut_resa"] == 0
    assert data["statut_nom"] == "en attente"
    assert data["resa_heure"] == "14:30:00"


def test_ajouter_enregistreDansLaBase(base):
    client.post("/reservations", json=RESA)
    conn = sqlite3.connect(base)
    nb = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    conn.close()
    assert nb == 1


def test_clientIntrouvable(base):
    assert client.post("/reservations", json={**RESA, "uid_client": 99}).status_code == 404


def test_zoneIntrouvable(base):
    assert client.post("/reservations", json={**RESA, "resa_DO_locationID": 999}).status_code == 404


def test_dateDansLePasse(base):
    assert client.post("/reservations", json={**RESA, "resa_date": "2020-01-01"}).status_code == 400


def test_donneesInvalides(base):
    assert client.post("/reservations", json={**RESA, "resa_heure": "25:00"}).status_code == 422
    assert client.post("/reservations", json={**RESA, "estimation_duree_course": -5}).status_code == 422


def test_detail(base):
    uid = client.post("/reservations", json=RESA).json()["uid_reservation"]
    assert client.get(f"/reservations/{uid}").status_code == 200
    assert client.get("/reservations/999").status_code == 404


def test_changerStatut(base):
    uid = client.post("/reservations", json=RESA).json()["uid_reservation"]
    assert client.patch(f"/reservations/{uid}/statut", json={"statut": 2}).status_code == 409
    assert client.patch(f"/reservations/{uid}/statut", json={"statut": 1}).json()["statut_nom"] == "confirmée"