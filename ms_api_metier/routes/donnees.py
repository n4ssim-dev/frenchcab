from fastapi import APIRouter, HTTPException, Query

from dlFichiers import RAW_DIR, convertCsv, downloadData

router = APIRouter(prefix="/donnees", tags=["donnees"])

MOIS_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("")
def listerFichiers():
    if not RAW_DIR.exists():
        return []
    return sorted(f.name for f in RAW_DIR.iterdir() if f.is_file())


# def (et non async def) : requests est bloquant, FastAPI l'exécute dans un thread
@router.post("/telechargement", status_code=201)
def telechargerMois(
    mois: str = Query("2026-07", pattern=MOIS_PATTERN, description="Format AAAA-MM"),
    csv: bool = False,
):
    fichier = downloadData(mois=mois)
    if fichier is None:
        raise HTTPException(status_code=502, detail=f"Données indisponibles pour {mois}")

    reponse = {"mois": mois, "parquet": fichier.name}
    if csv:
        reponse["csv"] = convertCsv(fichier).name
    return reponse
