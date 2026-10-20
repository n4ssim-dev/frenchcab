import hashlib
import sys
import types

from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestRegressor

from main import app

client = TestClient(app)


def test_info_modele(tmp_path, monkeypatch):
    fichier = tmp_path / "model_duree_premier.joblib"
    fichier.write_bytes(b"contenu de test")
    faux_predict = types.SimpleNamespace(
        MODEL_PATH=fichier,
        bundle={
            "nom_modele": "Random Forest",
            "metriques": {"MAE (min)": 3.39, "RMSE (min)": 5.1, "R2": 0.7},
        },
        model=RandomForestRegressor(),
        COLONNES=["distance", "heure"],
    )
    monkeypatch.setitem(sys.modules, "predict", faux_predict)

    reponse = client.get("/modele/info")

    assert reponse.status_code == 200
    donnees = reponse.json()
    md5 = hashlib.md5(b"contenu de test").hexdigest()
    assert donnees["nom_modele"] == "Random Forest"
    assert donnees["algorithme"] == "RandomForestRegressor"
    assert donnees["version"] == md5[:8]
    assert donnees["empreinte_md5"] == md5
    assert donnees["fichier"] == "model_duree_premier.joblib"
    assert donnees["nombre_variables"] == 2
    assert donnees["metriques"] == {"mae_minutes": 3.39, "rmse_minutes": 5.1, "r2": 0.7}


def test_info_modele_sans_metriques_ni_nom(tmp_path, monkeypatch):
    """Ancien format de modele : ni nom ni metriques dans le fichier."""
    fichier = tmp_path / "model_duree.joblib"
    fichier.write_bytes(b"ancien modele")
    faux_predict = types.SimpleNamespace(
        MODEL_PATH=fichier, bundle={}, model=RandomForestRegressor(), COLONNES=["a"]
    )
    monkeypatch.setitem(sys.modules, "predict", faux_predict)

    donnees = client.get("/modele/info").json()

    assert donnees["nom_modele"] == "RandomForestRegressor"
    assert donnees["metriques"] == {}
