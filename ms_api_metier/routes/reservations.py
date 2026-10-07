import sqlite3
from datetime import date, datetime, time

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from load import DB_PATH
router = APIRouter(prefix="/reservations", tags=["reservations"])

#statuts
EN_ATTENTE = 0
CONFIRMEE = 1
TERMINEE = 2
ANNULEE = 3

NOMS_STATUTS = {EN_ATTENTE: "en attente", CONFIRMEE: "confirmée",
                TERMINEE: "terminée", ANNULEE: "annulée"}

# Changements de statut(tatut actuel -> statuts possibles)
# "terminée" et "annulée" sont des statuts FINAUX
TRANSITIONS = {
    EN_ATTENTE: {CONFIRMEE, ANNULEE},
    CONFIRMEE: {TERMINEE, ANNULEE},
    TERMINEE: set(),
    ANNULEE: set(),
}


# modèles pydantic la forme des données envoyées par le client
class NouvelleReservation(BaseModel):
    uid_client: int = Field(gt=0)
    resa_PU_locationID: int = Field(gt=0, description="Zone de départ")
    resa_DO_locationID: int = Field(gt=0, description="Zone d'arrivée")
    resa_date: date = Field(description="Format AAAA-MM-JJ")
    resa_heure: time = Field(description="Format HH:MM")
    estimation_duree_course: float = Field(gt=0, description="En minutes")


class ChangementStatut(BaseModel):
    statut: int = Field(ge=0, le=3, description="0 attente, 1 confirmée, 2 terminée, 3 annulée")


def connexion():
    if not DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Base absente, lancez load.py")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # pour lire les lignes comme des dictionnaires
    return conn


def existe(conn, requete, valeur):
    return conn.execute(requete, (valeur,)).fetchone() is not None


def lire_reservation(conn, uid):
    ligne = conn.execute(
        "SELECT * FROM reservations WHERE uid_reservation = ?", (uid,)
    ).fetchone()
    if ligne is None:
        raise HTTPException(status_code=404, detail=f"Réservation {uid} introuvable")
    resa = dict(ligne)
    resa["statut_nom"] = NOMS_STATUTS[resa["statut_resa"]]
    return resa


#routes
@router.post("", status_code=201)
def ajouterReservation(resa: NouvelleReservation):
    depart = datetime.combine(resa.resa_date, resa.resa_heure)
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
            resa.resa_date.isoformat(),                      # "2026-10-08"
            resa.resa_heure.strftime("%H:%M:%S"),            # "14:30:00"
            resa.estimation_duree_course,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),    # réservé maintenant
            EN_ATTENTE,                                      # toujours "en attente" au départ
            resa.uid_client,
        ))
        conn.commit()
        return lire_reservation(conn, curseur.lastrowid)
    finally:
        conn.close()


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
        resa = lire_reservation(conn, uid_reservation)   # 404 si elle n'existe pas
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