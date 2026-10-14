from model_info import charger_infos_modele
from evaluation_model import main_evaluation
from train_ml_models import main_train
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
ML_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

RAPPORT_ENTRAINEMENT_PATH = DATA_DIR / "evaluation" / "rapport_entrainement_modeles.json"
EVALUATION_PATH = DATA_DIR / "evaluation" / "evaluation.json"

# appelle les deux
# produit le JSON final
# exit(0) ou exit(1)
def lire_dernier_run(path):
    with open(path, encoding="utf-8") as f:
        lignes = [ligne for ligne in f if ligne.strip()]
    return json.loads(lignes[-1])


def prepa_rapport_final():
    rapport_entrainement = lire_dernier_run(RAPPORT_ENTRAINEMENT_PATH)
    rapport_evaluation = lire_dernier_run(EVALUATION_PATH)

    entrainement_prepa = []
    evaluation_prepa = []
    for modele in rapport_entrainement.values():
        entrainement_prepa.append({
            "nom_modele" : modele["algorithme"],
            "date_entrainement" : modele["date_entrainement"],
            "metrique_mae_minutes" : modele["metriques"]["mae_minutes"],
            "metrique_rmse_minutes" : modele["metriques"]["rmse_minutes"],
            "metrique_r2" : modele["metriques"]["r2"],
            "metrique_mae_naif_minutes" : modele["metriques"]["mae_naif_minutes"],
        })

    for modele in rapport_evaluation.values():
        evaluation_prepa.append({
            "nom_modele": modele["algorithme"],
            "date_debut_donnees": modele["date_debut_donnees"],
            "nb_trajets": modele["nb_trajets"],
            "mae_minutes": modele["mae_minutes"],
            "date_evaluation": modele["date_evaluation"],
            "seuil_minutes": modele["seuil_minutes"],
            "seuil_respecte": modele["seuil_respecte"]
        })

    prepa_rapport_final = []
    if entrainement_prepa[0]["nom_modele"] == evaluation_prepa[0]["nom_modele"]:
        prepa_rapport_final.append(
            {
                "modele_choisi" : {
                    "nom_modele" : entrainement_prepa[0]["nom_modele"],
                    "date_entrainement" : entrainement_prepa[0]["date_entrainement"],
                    "date_evaluation": evaluation_prepa[0]["date_evaluation"],
                    "date_debut_donnees_eval": evaluation_prepa[0]["date_debut_donnees"],
                    "nb_trajets_eval": evaluation_prepa[0]["nb_trajets"],
                    "metrique_mae_minutes_entrainement" : entrainement_prepa[0]["metrique_mae_minutes"],
                    "mae_minutes_eval": evaluation_prepa[0]["mae_minutes"],
                    "delta_mae_minutes" : evaluation_prepa[0]["mae_minutes"] - entrainement_prepa[0]["metrique_mae_minutes"],
                    "seuil_minutes_eval": evaluation_prepa[0]["seuil_minutes"],
                    "seuil_respecte_eval": evaluation_prepa[0]["seuil_respecte"]
                }, "modele_secondaire": {
                    "nom_modele" : entrainement_prepa[1]["nom_modele"],
                    "date_entrainement" : entrainement_prepa[1]["date_entrainement"],
                    "date_evaluation": evaluation_prepa[1]["date_evaluation"],
                    "date_debut_donnees_eval": evaluation_prepa[1]["date_debut_donnees"],
                    "nb_trajets_eval": evaluation_prepa[1]["nb_trajets"],
                   "metrique_mae_minutes_entrainement" : entrainement_prepa[1]["metrique_mae_minutes"],
                    "mae_minutes_eval": evaluation_prepa[1]["mae_minutes"],
                    "delta_mae_minutes" : evaluation_prepa[1]["mae_minutes"] - entrainement_prepa[1]["metrique_mae_minutes"],
                    "seuil_minutes_eval": evaluation_prepa[1]["seuil_minutes"],
                    "seuil_respecte_eval": evaluation_prepa[1]["seuil_respecte"]
                }
            })
    return prepa_rapport_final



def main():
    # contrôle du seuil et date debut
    DATE_DEBUT_EVALUATION = "2026-07-28"
    SEUIL_MAE_MINUTES = 6.0

    #run train_model_extra
    main_train()

    #run evaluation
    main_evaluation(DATE_DEBUT_EVALUATION, SEUIL_MAE_MINUTES)
    #run prepation rapport
    dict_final = prepa_rapport_final()

    #creation json rapport final
    maintenant = datetime.now()
    RAPPORT_FINAL = DATA_DIR / "evaluation" / f"rapport_final_{maintenant.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(RAPPORT_FINAL, "a", encoding="utf-8") as f:
        json.dump({"date_rapport" : maintenant.isoformat() ,"rapport" : dict_final}, f, indent=4, ensure_ascii=False)
        
    
    # affichage

if __name__ == "__main__":
    main()