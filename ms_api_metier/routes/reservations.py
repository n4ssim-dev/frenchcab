import sqlite3
from datetime import date, datetime, time

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from load import DB_PATH

router = APIRouter(prefix="/reservations", tags=["reservations"])

# statuts
EN_ATTENTE = 0
CONFIRMEE = 1
TERMINEE = 2
ANNULEE = 3

NOMS_STATUTS = {EN_ATTENTE: "en attente", CONFIRMEE: "confirmée",
                TERMINEE: "terminée", ANNULEE: "annulée"}

# changements de statut (statut actuel -> statuts possibles)
# "terminée" et "annulée" sont des statuts FINAUX
TRANSITIONS = {
    EN_ATTENTE: {CONFIRMEE, ANNULEE},
    CONFIRMEE: {TERMINEE, ANNULEE},
    TERMINEE: set(),
    ANNULEE: set(),
}


# modèles pydantic : la forme des données envoyées par le client
class NouvelleReservation(BaseModel):
    uid_client: int = Field(gt=0)
    resa_PU_locationID: int = Field(gt=0, description="Zone de départ")
    resa_DO_locationID: int = Field(gt=0, description="Zone d'arrivée")
    resa_date: date = Field(description="Format AAAA-MM-JJ")
    resa_heure: time = Field(description="Format HH:MM")
    estimation_duree_course: float = Field(gt=0, description="En minutes")

    # Exemple pré-rempli dans Swagger (/docs) quand on clique sur "Try it out"
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "uid_client": 1,
                "resa_PU_locationID": 132,
                "resa_DO_locationID": 161,
                "resa_date": "2026-12-01",
                "resa_heure": "14:30",
                "estimation_duree_course": 35,
            }]
        }
    }


class ChangementStatut(BaseModel):
    statut: int = Field(ge=0, le=3, description="0 attente, 1 confirmée, 2 terminée, 3 annulée")


# outils base de données
def connexion():
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base absente, lancez load.py")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # pour lire les lignes comme des dictionnaires
    return conn


def existe(conn, requete, valeur):
    return conn.execute(requete, (valeur,)).fetchone() is not None


def en_dict(ligne):
    """Transforme une ligne SQLite en dictionnaire + ajoute le nom du statut."""
    resa = dict(ligne)
    resa["statut_nom"] = NOMS_STATUTS[resa["statut_resa"]]
    return resa


def lire_reservation(conn, uid):
    ligne = conn.execute(
        "SELECT * FROM reservations WHERE uid_reservation = ?", (uid,)
    ).fetchone()
    if ligne is None:
        raise HTTPException(status_code=404, detail=f"Réservation {uid} introuvable")
    return en_dict(ligne)


@router.post("", status_code=201)
def ajouterReservation(resa: NouvelleReservation):
    # On enlève le fuseau horaire ("14:30:00Z" -> 14:30:00), sinon erreur 500
    heure = resa.resa_heure.replace(tzinfo=None)
    depart = datetime.combine(resa.resa_date, heure)
    if depart < datetime.now():
        raise HTTPException(status_code=400, detail="La date de départ est dans le passé")

    conn = connexion()
    try:
        if not existe(conn, "SELECT 1 FROM clients WHERE uid_client = ?", resa.uid_client):
            raise HTTPException(status_code=404, detail=f"Client {resa.uid_client} introuvable")
        for zone in (resa.resa_PU_locationID, resa.resa_DO_locationID):
            if not existe(conn, "SELECT 1 FROM lieux WHERE locationID = ?", zone):
                raise HTTPException(status_code=404, detail=f"Zone {zone} introuvable")

        curseur = conn.execute("""
            INSERT INTO reservations (
                resa_PU_locationID, resa_DO_locationID, resa_date, resa_heure,
                estimation_duree_course, date_heure_reservation, statut_resa, uid_client
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resa.resa_PU_locationID,
            resa.resa_DO_locationID,
            resa.resa_date.isoformat(),                      # "2026-12-01"
            heure.strftime("%H:%M:%S"),                      # "14:30:00"
            resa.estimation_duree_course,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),    # réservé maintenant
            EN_ATTENTE,                                      # toujours "en attente" au départ
            resa.uid_client,
        ))
        conn.commit()
        return lire_reservation(conn, curseur.lastrowid)
    finally:
        conn.close()


@router.get("")
def listerReservations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    uid_client: int | None = Query(None, gt=0, description="Filtrer par client"),
    statut: int | None = Query(None, ge=0, le=3, description="0 attente, 1 confirmée, 2 terminée, 3 annulée"),
):
    # On construit le WHERE seulement avec les filtres demandés
    conditions = []
    params = []
    if uid_client is not None:
        conditions.append("uid_client = ?")
        params.append(uid_client)
    if statut is not None:
        conditions.append("statut_resa = ?")
        params.append(statut)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    conn = connexion()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM reservations{where}", params).fetchone()[0]
        lignes = conn.execute(
            f"SELECT * FROM reservations{where} ORDER BY uid_reservation DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    finally:
        conn.close()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "reservations": [en_dict(ligne) for ligne in lignes],
    }


@router.get("/{uid_reservation}")
def detailReservation(uid_reservation: int = Path(gt=0)):
    conn = connexion()
    try:
        return lire_reservation(conn, uid_reservation)
    finally:
        conn.close()


@router.patch("/{uid_reservation}/statut")
def changerStatut(changement: ChangementStatut, uid_reservation: int = Path(gt=0)):
    conn = connexion()
    try:
        resa = lire_reservation(conn, uid_reservation)  # 404 si elle n'existe pas
        actuel, nouveau = resa["statut_resa"], changement.statut

        if nouveau not in TRANSITIONS[actuel]:
            raise HTTPException(
                status_code=409,
                detail=f"Impossible de passer de '{NOMS_STATUTS[actuel]}' à '{NOMS_STATUTS[nouveau]}'",
            )

        conn.execute(
            "UPDATE reservations SET statut_resa = ? WHERE uid_reservation = ?",
            (nouveau, uid_reservation),
        )
        conn.commit()
        return lire_reservation(conn, uid_reservation)
    finally:
        conn.close()