import duckdb
from fastapi import APIRouter, HTTPException, Path, Query

from dlFichiers import RAW_DIR

router = APIRouter(prefix="/courses", tags=["courses"])

DB_PATH = RAW_DIR.parent / "yellow_taxi.db"

# La table n'a pas de clé : le rowid de DuckDB sert d'identifiant de course.
# Il est réattribué à chaque exécution de l'ETL (CREATE OR REPLACE TABLE).
SELECT_COURSES = """
    SELECT t.rowid AS id,
           t.VendorID AS vendor_id,
           t.tpep_pickup_datetime AS depart,
           t.tpep_dropoff_datetime AS arrivee,
           t.passenger_count AS passagers,
           t.trip_distance AS distance,
           t.PULocationID AS zone_depart_id,
           zd.Zone AS zone_depart,
           zd.Borough AS quartier_depart,
           t.DOLocationID AS zone_arrivee_id,
           za.Zone AS zone_arrivee,
           za.Borough AS quartier_arrivee,
           t.total_amount AS montant
    FROM yellowtripdata t
    LEFT JOIN taxi_zones zd ON zd.LocationID = t.PULocationID
    LEFT JOIN taxi_zones za ON za.LocationID = t.DOLocationID
"""


def connexion():
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base absente, lancez POST /donnees/etl")
    try:
        return duckdb.connect(str(DB_PATH), read_only=True)
    except duckdb.IOException:
        # Un autre processus (CLI, ETL en cours) détient le verrou d'écriture
        raise HTTPException(status_code=503, detail="Base verrouillée, réessayez plus tard")


def lignesEnDict(resultat):
    colonnes = [c[0] for c in resultat.description]
    return [dict(zip(colonnes, ligne)) for ligne in resultat.fetchall()]


@router.get("")
def listerCourses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    with connexion() as con:
        total = con.execute("SELECT COUNT(*) FROM yellowtripdata").fetchone()[0]
        courses = lignesEnDict(
            con.execute(f"{SELECT_COURSES} ORDER BY t.rowid LIMIT ? OFFSET ?", [limit, offset])
        )
    return {"total": total, "limit": limit, "offset": offset, "courses": courses}


@router.get("/{course_id}")
def detailCourse(course_id: int = Path(ge=0)):
    with connexion() as con:
        courses = lignesEnDict(con.execute(f"{SELECT_COURSES} WHERE t.rowid = ?", [course_id]))
    if not courses:
        raise HTTPException(status_code=404, detail=f"Course {course_id} introuvable")
    return courses[0]
