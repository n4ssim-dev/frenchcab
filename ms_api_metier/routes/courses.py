import duckdb
from fastapi import APIRouter, HTTPException, Path, Query

from dlFichiers import RAW_DIR

router = APIRouter(prefix="/courses", tags=["courses"])

DB_PATH = RAW_DIR.parent / "yellow_taxi.db"


# ============================================================
# Requête principale
# ============================================================
SELECT_COURSES = """
    SELECT
        t.id_trajet AS id,

        -- Informations temporelles
        td.date_heure AS depart,
        ta.date_heure AS arrivee,

        -- Informations départ
        ld.id_location AS zone_depart_id,
        ld.zone AS zone_depart,
        ld.arrondissement AS quartier_depart,
        ld.zone_service AS zone_service_depart,

        -- Informations arrivée
        la.id_location AS zone_arrivee_id,
        la.zone AS zone_arrivee,
        la.arrondissement AS quartier_arrivee,
        la.zone_service AS zone_service_arrivee,

        -- Informations course
        t.nb_passagers AS passagers,
        t.distance AS distance,
        t.duree_minutes AS duree,
        t.montant_total AS montant,

        -- Informations complémentaires
        t.id_vendeur AS vendor_id,
        t.id_tarif AS tarif_id,
        t.type_paiement AS type_paiement,
        t.store_and_fwd_flag AS store_and_fwd_flag,
        t.pourboire AS pourboire,
        t.peages AS peages

    FROM fait_trajets t

    LEFT JOIN dim_temps td
        ON td.id_temps = t.id_temps_depart

    LEFT JOIN dim_temps ta
        ON ta.id_temps = t.id_temps_arrivee

    LEFT JOIN dim_location ld
        ON ld.id_location = t.id_location_depart

    LEFT JOIN dim_location la
        ON la.id_location = t.id_location_arrivee
"""


# ============================================================
# Connexion DuckDB
# ============================================================
def connexion():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Base absente, lancez POST /donnees/etl"
        )

    try:
        return duckdb.connect(str(DB_PATH), read_only=True)

    except duckdb.IOException:
        raise HTTPException(
            status_code=503,
            detail="Base verrouillée, réessayez plus tard"
        )


# ============================================================
# Conversion resultat -> dictionnaires
# ============================================================
def lignesEnDict(resultat):
    colonnes = [c[0] for c in resultat.description]

    return [
        dict(zip(colonnes, ligne))
        for ligne in resultat.fetchall()
    ]


# ============================================================
# Liste des courses
# ============================================================
@router.get("")
def listerCourses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    date: str | None = Query(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$"
    )
):
    where = ""
    params = []

    # Filtre sur la date de départ
    if date is not None:
        where = "WHERE td.date = ?"
        params.append(date)

    with connexion() as con:

        # ----------------------------------------------------
        # Nombre total de courses
        # ----------------------------------------------------
        total_query = f"""
            SELECT COUNT(*)
            FROM fait_trajets t
            LEFT JOIN dim_temps td
                ON td.id_temps = t.id_temps_depart
            {where}
        """

        total = con.execute(
            total_query,
            params
        ).fetchone()[0]

        # ----------------------------------------------------
        # Récupération des courses
        # ----------------------------------------------------
        courses_query = f"""
            {SELECT_COURSES}
            {where}
            ORDER BY t.id_trajet
            LIMIT ?
            OFFSET ?
        """

        courses = lignesEnDict(
            con.execute(
                courses_query,
                params + [limit, offset]
            )
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "courses": courses
    }


# ============================================================
# Detail d'une course
# ============================================================
@router.get("/{course_id}")
def detailCourse(
    course_id: int = Path(ge=0)
):
    with connexion() as con:

        query = f"""
            {SELECT_COURSES}
            WHERE t.id_trajet = ?
        """

        courses = lignesEnDict(
            con.execute(
                query,
                [course_id]
            )
        )

    if not courses:
        raise HTTPException(
            status_code=404,
            detail=f"Course {course_id} introuvable"
        )

    return courses[0]
