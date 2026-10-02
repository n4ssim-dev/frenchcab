from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/predictions", tags=["predictions"])


class DemandePrediction(BaseModel):
    pickup: datetime
    id_location_depart: int
    id_location_arrivee: int
    distance: float = Field(gt=0)


@router.post("/duree")
def predireDuree(demande: DemandePrediction):
    # import ici : le modèle n'est chargé qu'à la première prédiction,
    # pour que l'API démarre même si model_duree.joblib est absent
    from predict import predire_duree

    try:
        resultat = predire_duree(pd.DataFrame([demande.model_dump()]))
    except ValueError as e:  # zone inconnue
        raise HTTPException(status_code=422, detail=str(e))
    return {"duree_predite_min": float(resultat.iloc[0])}