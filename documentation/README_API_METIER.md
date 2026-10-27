# ms_api_metier

Le cerveau de FrenchCab (port **8000**), en Python : il prépare les données, gère les réservations et calcule les prédictions de durée de trajet.

| Documentation détaillée | Contenu |
|---|---|
| [README_DONNEES](README_DONNEES.md) | Les bases de données, `load.py`, l'API des réservations et leurs tests |
| [README_ML](README_ML.md) | La prédiction de durée et le pipeline d'entraînement (`ml/`) |
| [README_MLOPS](README_MLOPS.md) | DVC, MLflow et déploiement d'un modèle sur la VM |

## Fichiers importants

| Fichier / dossier | À quoi ça sert |
|---|---|
| `dlFichiers.py` | Télécharge les données brutes et les convertit en CSV |
| `etl.py` | Nettoie les données et crée la base `yellow_taxi.db` |
| `load.py` | Crée et remplit la base `frenchcab.db` (clients, réservations, trajets) |
| `main.py` | Démarre l'API (avec `uvicorn`) |
| `routes/reservations.py` | Les routes des réservations |
| `predict.py` | La fonction `predire_duree()` pour prédire la durée d'un trajet |
| `ml/` | Entraînement, évaluation et suivi des modèles de machine learning |
| `tests/` | Les tests automatiques |
| `data/` | Les données, bases et modèles (volumineux, gérés avec DVC) |
| `dvc.yaml`, `params.yaml` | Description du pipeline reproductible et de ses paramètres |

## Environnement Python

```bash
cd ms_api_metier
python3 -m venv .venv
source .venv/Scripts/activate        # Windows (Git Bash). Sous Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ml.txt   # seulement pour le ML (dvc + mlflow)
```

## Préparer les données (étapes dans l'ordre)

Depuis le dossier `ms_api_metier`. **L'ordre compte** : chaque étape a besoin du résultat de la précédente.

```bash
python dlFichiers.py   # 1. télécharge les données brutes (+ conversion CSV)
python etl.py          # 2. nettoie → crée yellow_taxi.db et le CSV « propre »
python load.py         # 3. crée et remplit frenchcab.db
```

Bon à savoir :

- `load.py` peut être relancé à volonté : il **vide les tables avant de les remplir** (pas de doublons).
- À chaque nouvelle donnée téléchargée, relance `etl.py` **avant** `load.py`.
- Résultat attendu de `load.py` : 265 lieux, 15 clients, 50 000 réservations, 3 527 158 trajets.
- Pour vérifier : `python stats_clients.py`. Alice Martin doit apparaître en premier (le plus de trajets) et Océane Petit en dernier.

Le détail des bases et du nettoyage est dans [README_DONNEES](README_DONNEES.md).

## Démarrer l'API en local

```bash
uvicorn main:app --reload
```

La documentation interactive (Swagger) est alors sur http://127.0.0.1:8000/docs, où l'on peut tester chaque route directement.

## Les tests automatiques

À lancer depuis `ms_api_metier` :

```bash
python -m pytest                                # tous les tests
python -m pytest tests/test_load.py -v          # tests de load.py
python -m pytest tests/test_reservations.py -v  # tests des réservations
```

**Principe commun : les tests ne touchent jamais les vraies bases.** Chaque test travaille dans un dossier temporaire avec de mini-données inventées, ce qui le rend rapide et sans risque.

| Fichier | Attendu | Ce qu'il vérifie | Détail |
|---|---|---|---|
| `test_load.py` | `10 passed` | Création des 4 tables, hachage des mots de passe, nombres de lignes, conversions (`Y` → 1, cases vides → valeurs par défaut), colonnes calculées, clés étrangères, liens réservations/trajets, absence de doublons si on relance l'import | [test_load.py](README_DONNEES.md#test_loadpy) |
| `test_reservations.py` | `22 passed` | Les routes appelées comme le ferait le front : création (201), erreurs (400, 404, 422), liste (filtres, ordre, pagination), détail, changements de statut (chemin normal, sauts interdits 409) | [test_reservations.py](README_DONNEES.md#test_reservationspy) |

**Comment lire un échec** : le nom du test indique quoi regarder. Par exemple `test_ajouter_...` → fonction `ajouterReservation`, `test_statut_...` → `changerStatut`, `test_relancer_...` → `vider_tables`.
