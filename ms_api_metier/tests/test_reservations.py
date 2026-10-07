import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import load
from main import app

client = TestClient(app)

# Une réservation valide (date loin dans le futur pour que le test reste valable)
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
    """Base temporaire : 2 clients, 2 zones, aucune réservation."""
    chemin = tmp_path / "frenchcab.db"
    monkeypatch.setattr(load, "DB_PATH", chemin)
    load.creer_base_si_inexistante()

    conn = sqlite3.connect(chemin)
    conn.executemany("INSERT INTO clients VALUES (?, ?, ?, 'x')",
                     [(1, "Alice", "a@mail.fr"), (2, "Bruno", "b@mail.fr")])
    conn.executemany("INSERT INTO lieux VALUES (?, 'Queens', 'Zone', 'Boro Zone')", [(1,), (2,)])
    conn.commit()
    conn.close()

    with patch("routes.reservations.DB_PATH", chemin):
        yield chemin


def ajouter(**changements):
    """Ajoute une réservation (RESA + changements) et renvoie la réponse."""
    return client.post("/reservations", json={**RESA, **changements})


# ---------------------------------------------------------------------------
# POST /reservations
# ---------------------------------------------------------------------------
def test_ajouter_ok(base):
    r = ajouter()
    assert r.status_code == 201
    data = r.json()
    assert data["uid_reservation"] == 1
    assert data["statut_resa"] == 0
    assert data["statut_nom"] == "en attente"
    assert data["resa_heure"] == "14:30:00"


def test_ajouter_heureAvecFuseau(base):
    # Swagger peut envoyer "14:30:00Z" : ne doit pas faire d'erreur 500
    r = ajouter(resa_heure="14:30:00Z")
    assert r.status_code == 201
    assert r.json()["resa_heure"] == "14:30:00"


def test_ajouter_enregistreDansLaBase(base):
    ajouter()
    conn = sqlite3.connect(base)
    nb = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
    conn.close()
    assert nb == 1


def test_ajouter_clientIntrouvable(base):
    assert ajouter(uid_client=99).status_code == 404


def test_ajouter_zoneIntrouvable(base):
    assert ajouter(resa_DO_locationID=999).status_code == 404


def test_ajouter_dateDansLePasse(base):
    assert ajouter(resa_date="2020-01-01").status_code == 400


def test_ajouter_donneesInvalides(base):
    assert ajouter(resa_heure="25:00").status_code == 422
    assert ajouter(estimation_duree_course=-5).status_code == 422
    assert ajouter(uid_client=0).status_code == 422


# ---------------------------------------------------------------------------
# GET /reservations  (liste)
# ---------------------------------------------------------------------------
@pytest.fixture
def trois_resas(base):
    """3 réservations : 1 et 2 pour Alice, 3 pour Bruno. La 1 est confirmée."""
    ajouter()
    ajouter()
    ajouter(uid_client=2)
    client.patch("/reservations/1/statut", json={"statut": 1})
    return base


def test_liste_vide(base):
    data = client.get("/reservations").json()
    assert data["total"] == 0
    assert data["reservations"] == []


def test_liste_tout_plusRecenteEnPremier(trois_resas):
    data = client.get("/reservations").json()
    assert data["total"] == 3
    assert [r["uid_reservation"] for r in data["reservations"]] == [3, 2, 1]
    assert "statut_nom" in data["reservations"][0]


def test_liste_filtreClient(trois_resas):
    assert client.get("/reservations", params={"uid_client": 1}).json()["total"] == 2
    assert client.get("/reservations", params={"uid_client": 2}).json()["total"] == 1


def test_liste_filtreStatut(trois_resas):
    assert client.get("/reservations", params={"statut": 0}).json()["total"] == 2
    assert client.get("/reservations", params={"statut": 1}).json()["total"] == 1


def test_liste_deuxFiltres(trois_resas):
    data = client.get("/reservations", params={"uid_client": 1, "statut": 0}).json()
    assert data["total"] == 1
    assert data["reservations"][0]["uid_reservation"] == 2


def test_liste_pagination(trois_resas):
    data = client.get("/reservations", params={"limit": 1, "offset": 1}).json()
    assert data["total"] == 3                      # le total ne change pas
    assert len(data["reservations"]) == 1
    assert data["reservations"][0]["uid_reservation"] == 2


def test_liste_parametresInvalides(base):
    assert client.get("/reservations", params={"statut": 7}).status_code == 422
    assert client.get("/reservations", params={"limit": 5000}).status_code == 422


# ---------------------------------------------------------------------------
# GET /reservations/{id}  (détail)
# ---------------------------------------------------------------------------
def test_detail_ok(base):
    uid = ajouter().json()["uid_reservation"]
    r = client.get(f"/reservations/{uid}")
    assert r.status_code == 200
    assert r.json()["uid_client"] == 1


def test_detail_introuvable(base):
    assert client.get("/reservations/999").status_code == 404


# ---------------------------------------------------------------------------
# PATCH /reservations/{id}/statut
# ---------------------------------------------------------------------------
def changer(uid, statut):
    return client.patch(f"/reservations/{uid}/statut", json={"statut": statut})


def test_statut_cheminNormal(base):
    uid = ajouter().json()["uid_reservation"]
    assert changer(uid, 1).json()["statut_nom"] == "confirmée"
    assert changer(uid, 2).json()["statut_nom"] == "terminée"


def test_statut_annulerDepuisAttente(base):
    uid = ajouter().json()["uid_reservation"]
    assert changer(uid, 3).json()["statut_nom"] == "annulée"


def test_statut_sautInterdit(base):
    uid = ajouter().json()["uid_reservation"]
    assert changer(uid, 2).status_code == 409      # en attente -> terminée : interdit


def test_statut_finalBloque(base):
    uid = ajouter().json()["uid_reservation"]
    changer(uid, 3)                                # annulée
    assert changer(uid, 0).status_code == 409
    assert changer(uid, 1).status_code == 409


def test_statut_introuvable(base):
    assert changer(999, 1).status_code == 404


def test_statut_invalide(base):
    uid = ajouter().json()["uid_reservation"]
    assert changer(uid, 7).status_code == 422