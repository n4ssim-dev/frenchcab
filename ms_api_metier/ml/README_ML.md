# Dossier `ml/`

Scripts d'entraînement, d'évaluation et de suivi (MLOps) des modèles qui prédisent la **durée d'un trajet en taxi (en minutes)**

## Prérequis

La base DuckDB `data/yellow_taxi.db` doit exister et contenir les tables `fait_trajets`, `dim_temps`, `dim_location` et `features_creneau`

Elles sont créées par `etl.py` :

```bash
cd ms_api_metier
python dlFichiers.py   # téléchargement des données brutes
python etl.py          # nettoyage + création de yellow_taxi.db
```

## Lancer le pipeline complet

Les scripts s'importent entre eux par leur nom (`from model_info import ...`), il faut donc les lancer **depuis le dossier `ml/`** :

```bash
cd ms_api_metier/ml
python run_mlops.py
```

## Les fichiers

|Fichier|Rôle|Lancement seul|
|-|-|-|
|`train_ml_models.py`|Entraîne et compare RandomForest et ExtraTrees, sauvegarde les deux modèles|via `main_train()`|
|`evaluation_model.py`|Évalue les deux modèles sauvegardés sur des données récentes et compare la MAE à un seuil|via `main_evaluation(date_debut, seuil)`|
|`run_mlops.py`|Enchaîne entraînement, évaluation puis produit le rapport final|`python run_mlops.py`|
|`model_info.py`|Affiche les informations d'un modèle sauvegardé (nom, métriques, version, nb de features)|`python model_info.py`|

### `train_ml_models.py`

Fonction principale : `main_train()`, en 11 étapes

1. Extraction des trajets depuis `yellow_taxi.db` (durée 1 à 180 min, distance 0,1 à 80 miles, premier jour exclu pour avoir des features de trafic complètes)
2. Matrice de corrélation -> `data/Matrices_correlation/Matrice_correlation_duree_trajet_ExtraTreesRegressor.png`
3. Variables ajoutées : `meme_zone`, `trajet_aeroport`, `creneau_sin` / `creneau_cos` (encodage cyclique des 48 créneaux de 30 min)
4. Découpage **temporel** 80 % train / 20 % test, encodage one-hot des arrondissements et zones de service, valeurs manquantes remplacées par la médiane du train
5. Deux modèles : `RandomForestRegressor` et `ExtraTreesRegressor` (100 arbres, profondeur max 20, `random_state=42`)
6. Entraînement des deux modèles
7. Comparaison sur MAE, RMSE et R², classement par MAE
8. Comparaison avec un modèle naïf (prédit toujours la moyenne du train)
9. Importance des variables du meilleur modèle (dont le poids total des variables de trafic)
10. Graphique des MAE -> `data/comparaison_modeles_duree.png`
11. Sauvegarde des modèles et du rapport

### `evaluation_model.py`

Fonction principale : `main_evaluation(date_debut, seuil)`

- recharge les trajets à partir de `date_debut`
- les prépare comme à l'entraînement (mêmes colonnes et médianes, lues dans l'artefact)
- calcule la MAE de chaque modèle et vérifie `mae <= seuil`
- renvoie `0` si le premier modèle respecte le seuil, `1` sinon

### `run_mlops.py`

1. `main_train()`
2. `main_evaluation("2026-07-28", 6.0)` : évaluation à partir du 28/07/2026, seuil de MAE à 6 minutes (valeurs modifiables dans `main()`)
3. assemble la dernière ligne du rapport d'entraînement et de celui d'évaluation dans un rapport final : MAE à l'entraînement, MAE à l'évaluation, écart (`delta_mae_minutes`) et respect du seuil, pour le modèle choisi et le modèle secondaire

### `model_info.py`

Charge `data/models/model_duree_extra_trees.joblib` et affiche son nom, ses métriques, la version de scikit-learn et le nombre de features

> Ce fichier n'est pas produit par `train_ml_models.py` (qui écrit `model_duree_premier.joblib` / `model_duree_deuxieme.joblib`) : il faut qu'il existe déjà dans `data/models/`

## Fichiers produits

|Fichier|Contenu|
|-|-|
|`data/models/model_duree_premier.joblib`|Meilleur modèle (plus petite MAE)|
|`data/models/model_duree_deuxieme.joblib`|Second modèle|
|`data/evaluation/rapport_entrainement_modeles.json`|Une ligne JSON ajoutée par entraînement (algorithme, date, MAE, RMSE, R², MAE naïve)|
|`data/evaluation/evaluation.json`|Une ligne JSON ajoutée par évaluation (MAE, nb de trajets, seuil, seuil respecté)|
|`data/evaluation/rapport_final_AAAA-MM-JJ_HH-MM-SS.json`|Rapport final d'un run de `run_mlops.py`|
|`data/Matrices_correlation/*.png`|Matrice de corrélation|
|`data/comparaison_modeles_duree.png`|Graphique de comparaison des MAE|

Chaque artefact `.joblib` est un dictionnaire :

|Clé|Contenu|
|-|-|
|`model`|Le modèle scikit-learn entraîné|
|`nom_modele`|`"Random Forest"` ou `"Extra Trees"`|
|`colonnes`|Liste et ordre des colonnes attendues en entrée|
|`mediane`|Médianes du train, pour remplacer les valeurs manquantes|
|`metriques` (1er) / `metriques_deuxieme` (2e)|MAE, RMSE et R² sur le jeu de test|
