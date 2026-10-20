import hashlib
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/modele", tags=["modele"])

CLES_METRIQUES = {"MAE (min)": "mae_minutes", "RMSE (min)": "rmse_minutes", "R2": "r2"}


@lru_cache(maxsize=4)
def _empreinte(chemin: str, taille: int, date_modif: float) -> str:
    """MD5 du fichier modele. Le cache est indexe sur la taille et la date :
    le calcul (quelques secondes pour 1,4 Go) n'est refait que si le fichier change."""
    md5 = hashlib.md5()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(8 * 1024 * 1024), b""):
            md5.update(bloc)
    return md5.hexdigest()


def _metriques(bundle: dict) -> dict:
    brutes = bundle.get("metriques") or bundle.get("metriques_deuxieme") or {}
    return {
        nouveau: round(float(brutes[ancien]), 4)
        for ancien, nouveau in CLES_METRIQUES.items()
        if ancien in brutes
    }


@router.get("/info")
def infoModele():
    """Nom, version et caracteristiques du modele de duree utilise par l'API."""
    # import ici, comme pour /predictions/duree : le modele est charge a la
    # premiere utilisation (cela peut prendre une minute pour un gros modele)
    try:
        import predict
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Modèle introuvable : {e}")

    chemin = Path(predict.MODEL_PATH)
    stat = chemin.stat()
    md5 = _empreinte(str(chemin), stat.st_size, stat.st_mtime)
    bundle = predict.bundle

    return {
        "nom_modele": bundle.get("nom_modele") or type(predict.model).__name__,
        "algorithme": type(predict.model).__name__,
        "version": md5[:8],
        "empreinte_md5": md5,
        "fichier": chemin.name,
        "date_fichier": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "nombre_variables": len(predict.COLONNES),
        "metriques": _metriques(bundle),
    }
