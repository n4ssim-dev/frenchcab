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
        response = client.post("/donnees/telechargement", params={"mois": "2026-05"})

    mock_dl.assert_called_once_with(mois="2026-05")
    assert response.status_code == 201
    assert response.json() == {"mois": "2026-05", "parquet": fichier.name}


def test_telechargementIndisponible():
    with patch("routes.donnees.downloadData", return_value=None):
        response = client.post("/donnees/telechargement", params={"mois": "2026-05"})

    assert response.status_code == 502


def test_moisInvalide():
    response = client.post("/donnees/telechargement", params={"mois": "2026-13"})

    assert response.status_code == 422
