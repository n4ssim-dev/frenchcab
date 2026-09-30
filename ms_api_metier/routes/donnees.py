import threading

from fastapi import APIRouter, HTTPException, Query

import etl
from dlFichiers import RAW_DIR, convertCsv, downloadData, downloadData2

router = APIRouter(prefix="/donnees", tags=["donnees"])

MOIS_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
DATA_DIR = RAW_DIR.parent

# etl.py lit ses chemins dans des variables globales : on les redéfinit avant
# chaque exécution, le verrou évite que deux requêtes se marchent dessus
etl_lock = threading.Lock()


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


@router.post("/zones", status_code=201)
def telechargerZones():
    fichier = downloadData2()
    if fichier is None:
        raise HTTPException(status_code=502, detail="Table des zones indisponible")
    return {"zones": fichier.name}


@router.post("/etl", status_code=201)
def lancerEtl(
    mois: str = Query("2026-07", pattern=MOIS_PATTERN, description="Format AAAA-MM"),
):
    csv_brut = RAW_DIR / f"yellow_tripdata_{mois}.csv"
    zones = RAW_DIR / "taxi_zone_lookup.csv"
    manquants = [f.name for f in (csv_brut, zones) if not f.exists()]
    if manquants:
        raise HTTPException(status_code=404, detail=f"Fichiers manquants : {', '.join(manquants)}")

    csv_propre = DATA_DIR / f"yellow_tripdata_{mois}_propre.csv"
    dossier_rejets = DATA_DIR / "lignes_rejetees"
    rejets = f"yellow_taxi_lignes_rejetees_{mois}.csv"
    base = DATA_DIR / "yellow_taxi.db"
    dossier_rejets.mkdir(parents=True, exist_ok=True)

    with etl_lock:
        etl.CSV_PATH = csv_brut
        etl.OUTPUT_PATH = csv_propre
        etl.dossier_sortie = dossier_rejets
        etl.REJETS_PATH = rejets
        etl.SQL_DB = base
        etl.ZONES_PATH = zones

        df = etl.nettoyage_csv(etl.lire_csv())
        etl.creer_db()

    return {
        "mois": mois,
        "lignes_propres": len(df),
        "csv_propre": csv_propre.name,
        "rejets": rejets,
        "base": base.name,
    }
