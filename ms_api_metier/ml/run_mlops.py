from model_info import charger_infos_modele
from evaluation_model import evaluer_modele, verifier_seuil

def main():

    infos = charger_infos_modele()

    resultat = evaluer_modele()

    # construction du JSON final

    # affichage

    # contrôle du seuil

if __name__ == "__main__":
    main()