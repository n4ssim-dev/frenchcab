# Commandes à executer
```
python3 -m venv .venv
. .venv/Scripts/activate 
pip install -r requirements.txt
```

# téléchargement des fichiers data

```
Executer le fichier dlFichiers.py présent dans le dossier ms_api_metier pour télécharger le fichier data utile et le convertir en csv. Un test vérifie la présence de fichiers générés.
```

# traitement et chargement des données
```
Executer le fichier etl.py présent dans le dossier ms_api_metier pour traiter les données et les envoyer vers yellow_taxi.db présent dans ms_api_metier/data.

```
# Composition de yellow_taxi.db
```
Base yellow_taxi.db (DuckDb) est composée de 2 tables, yellowtripdata comprenant toutes les courses et taxi_zones permettant de localiser les zones de prise en charge et de dépose des clients

# Pour lancer les tests
```
python -m pytest
```