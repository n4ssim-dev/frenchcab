# Guide de prise en main de FrenchCab (version débutant)

Ce document résume tous les README du projet et les explique simplement. Si un mot technique t'est inconnu, va voir le [petit lexique](#16-petit-lexique) à la fin.

---

## Sommaire

1. [Le projet en une minute](#1-le-projet-en-une-minute)
2. [L'architecture : 3 services](#2-larchitecture--3-services)
3. [Organisation du code](#3-organisation-du-code)
4. [Les données et les bases](#4-les-données-et-les-bases)
5. [Installer et lancer le projet](#5-installer-et-lancer-le-projet)
6. [Préparer les données (étapes dans l'ordre)](#6-préparer-les-données-étapes-dans-lordre)
7. [L'API des réservations](#7-lapi-des-réservations)
8. [La prédiction de durée (machine learning)](#8-la-prédiction-de-durée-machine-learning)
9. [DVC et MLflow : suivre données et expériences](#9-dvc-et-mlflow--suivre-données-et-expériences)
10. [Docker](#10-docker)
11. [Les tests automatiques](#11-les-tests-automatiques)
12. [CI/CD : automatiser](#12-cicd--automatiser)
13. [Déployer sur la VM](#13-déployer-sur-la-vm)
14. [Règles de travail en équipe](#14-règles-de-travail-en-équipe)
15. [Points à clarifier](#15-points-à-clarifier)
16. [Petit lexique](#16-petit-lexique)

---

## 1. Le projet en une minute

**FrenchCab** est une application qui exploite les données publiques des **taxis jaunes de New York** (« Yellow Taxi Trip Records », publiées par la TLC, l'autorité des taxis de la ville).

Elle permet de :

- importer et nettoyer ces données ;
- les stocker dans des bases de données ;
- les exposer via une **API** (un « guichet » que d'autres programmes peuvent interroger) ;
- les consulter sur un **site web** (avec pagination des résultats) ;
- gérer des **réservations** de taxi ;
- **prédire la durée d'un trajet** grâce à un modèle de machine learning.

L'application est déployée sur une machine virtuelle (VM), accessible en HTTPS.

Le projet a été pensé pour qu'une autre équipe puisse le reprendre sans l'aide de ceux qui l'ont écrit : c'est le but de ce guide.

---

## 2. L'architecture : 3 services

L'application est découpée en **3 microservices**, chacun dans son propre **conteneur** Docker (une petite boîte isolée qui contient un programme et tout ce dont il a besoin).

```
        Utilisateur (navigateur)
                 │
                 ▼
        ┌─────────────────┐
        │    ms_front     │   Site web (Angular)         port 80
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │     gateway     │   Point d'entrée de l'API    port 3000
        └────────┬────────┘
                 ▼
        ┌─────────────────┐
        │  ms_api_metier  │   Logique métier + données   port 8000
        │    (Python)     │   + modèle de prédiction
        └─────────────────┘
```

| Service | Rôle | Port |
|---|---|---|
| `ms_front` | L'interface web que voit l'utilisateur (écrite en Angular) | 80 |
| `gateway` | Le « standard téléphonique » : reçoit les demandes du front et les redirige vers le bon service | 3000 |
| `ms_api_metier` | Le cerveau : lit les données, gère les réservations, calcule les prédictions | 8000 |

La gateway parle à l'API métier à l'adresse interne `http://ms_api_metier:8000` (le nom du conteneur sert d'adresse dans le réseau Docker).

Routes principales exposées par la gateway :

| Méthode | Route | Description |
|---|---|---|
| GET | `/courses` | Liste toutes les courses de taxi |
| GET | `/courses/:id` | Détails d'une course |

---

## 3. Organisation du code

Le dépôt GitHub est : `https://github.com/n4ssim-dev/frenchcab.git`

**Frontend** (ce que voit l'utilisateur) : le dossier `ms_front`, en Angular. Il affiche les courses et dialogue avec la gateway.

**Backend** (ce qui travaille en coulisse) :

- `gateway` : le routage des requêtes ;
- `ms_api_metier` : tout le reste. Ses fichiers importants :

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

---

## 4. Les données et les bases

### Le chemin des données

```
Fichiers parquet (TLC)  →  CSV  →  nettoyage (etl.py)  →  bases de données
```

1. Les données sont d'abord téléchargées au format **parquet** (un format compact pour gros volumes), puis converties en **CSV**.
2. `etl.py` (ETL = Extraire, Transformer, Charger) nettoie ces données.
3. Elles sont ensuite rangées dans des bases.

### Les deux bases du projet

| Base | Type | Créée par | Contenu | Usage |
|---|---|---|---|---|
| `data/yellow_taxi.db` | DuckDB (analytique) | `etl.py` | Trajets, dimensions temps/lieux, caractéristiques de trafic | Entraîner les modèles de ML |
| `data/frenchcab.db` | SQLite (transactionnelle) | `load.py` | Lieux, clients, réservations, trajets | L'API des réservations |

> Les notes de départ mentionnent aussi une « base analytique PostgreSQL ». Elle n'apparaît dans aucun autre README : voir [Points à clarifier](#15-points-à-clarifier).

### Tables de `frenchcab.db`

```
clients ──< reservations >── trajets
              │    │            │
              └────┴── lieux ───┘
```

| Table | Contenu | Remplie avec |
|---|---|---|
| `lieux` | 265 zones de New York | `taxi_zone_lookup.csv` |
| `clients` | 15 clients d'exemple | écrits directement dans `load.py` |
| `reservations` | 50 000 réservations | générées à partir de trajets tirés au hasard |
| `trajets` | environ 3,5 millions de courses | `yellow_tripdata_2026-07_propre.csv` |

**Pourquoi des clients fictifs ?** Les données des taxis new-yorkais ne contiennent aucune info sur les clients. Pour pouvoir calculer des statistiques par client, le script invente 15 clients, chacun avec un « poids » (sa fréquence d'utilisation) : un client de poids 10 fait environ 10 fois plus de trajets qu'un client de poids 1. Les mots de passe sont stockés **hachés** (sha256), jamais en clair.

**Lien entre les tables** : `trajets.uid_reservation` → `reservations.uid_client` → `clients`.

### Nettoyage appliqué

- `etl.py` supprime les courses de plus de 320 miles ou de plus de 7 heures.
- `load.py` corrige aussi le CSV : renommage de colonnes, `Y`/`N` convertis en 1/0, cases vides remplacées par des valeurs par défaut (1 passager, tarif 99 = inconnu, frais à 0), calcul de la durée et de l'heure de départ, suppression des trajets dont la zone est inconnue.

---

## 5. Installer et lancer le projet

### Prérequis

- Docker et Docker Compose
- Git
- Un compte Docker Hub avec accès aux images du projet
- Pour travailler sur la partie Python en local : Python 3

### Installation

```bash
git clone https://github.com/n4ssim-dev/frenchcab.git
cd frenchcab
```

Puis créer les fichiers **`.env`** à partir des modèles fournis :

- le `.env` **à la racine** sert à Docker Compose (il remplit les variables de `docker-compose.yml`) ;
- le `gateway/.env` contient les variables du conteneur gateway.

⚠️ Ces fichiers contiennent des informations sensibles : **ne jamais les commiter dans Git**.

### Lancer avec les images publiées sur Docker Hub

```bash
docker compose pull      # récupère les dernières images
docker compose up -d     # démarre les conteneurs en arrière-plan
```

### Ou construire les images soi-même

```bash
docker compose build
docker compose up -d
```

### Environnement Python (pour `ms_api_metier`)

```bash
cd ms_api_metier
python3 -m venv .venv
. .venv/Scripts/activate        # Windows (Git Bash). Sous Linux/Mac : source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ml.txt   # seulement pour le ML (dvc + mlflow)
```

---

## 6. Préparer les données (étapes dans l'ordre)

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

Ensuite, pour démarrer l'API en local :

```bash
uvicorn main:app --reload
```

La documentation interactive (Swagger) est alors sur http://127.0.0.1:8000/docs, où l'on peut tester chaque route directement.

---

## 7. L'API des réservations

Code dans `routes/reservations.py`, tests dans `tests/test_reservations.py`.

### Les statuts d'une réservation

| Code | Nom |
|---|---|
| 0 | en attente |
| 1 | confirmée |
| 2 | terminée |
| 3 | annulée |

```
0 en attente ──► 1 confirmée ──► 2 terminée
     │                │
     └────────────────┴──► 3 annulée
```

Règles : une nouvelle réservation est toujours « en attente » ; on ne peut pas sauter de « en attente » à « terminée » ; « terminée » et « annulée » sont **finales**.

### Les 4 routes

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/reservations` | Créer une réservation |
| GET | `/reservations` | Lister (avec filtres `uid_client`, `statut` et pagination `limit`/`offset`) |
| GET | `/reservations/{uid_reservation}` | Voir une réservation |
| PATCH | `/reservations/{uid_reservation}/statut` | Changer le statut |

**Exemple de création** (`POST /reservations`) :

```json
{
  "uid_client": 1,
  "resa_PU_locationID": 132,
  "resa_DO_locationID": 161,
  "resa_date": "2026-12-01",
  "resa_heure": "08:30",
  "estimation_duree_course": 45
}
```

(`PU` = Pick-Up, lieu de prise en charge ; `DO` = Drop-Off, lieu de dépose.) L'API remplit toute seule le numéro de réservation, la date de la demande et le statut `0`.

**Exemple de changement de statut** : `PATCH /reservations/50001/statut` avec `{ "statut": 1 }`.

### Codes d'erreur à connaître

| Code | Signification |
|---|---|
| 200 / 201 | Succès / réservation créée |
| 400 | Date de départ dans le passé |
| 404 | Client, zone ou réservation introuvable |
| 409 | Changement de statut interdit |
| 422 | Données mal formées (ex. heure `25:00`, durée négative) |
| 503 | Base absente : lancer `load.py` |

### Pour essayer

Quelques identifiants utiles : clients 1 Alice Martin, 2 Bruno Lefevre, 3 Chloé Bernard ; zones 132 JFK Airport, 138 LaGuardia, 161 Midtown Center, 230 Times Square.

`python ajouter_reservations_test.py` crée 8 réservations de test (l'API doit tourner). Attention : les 50 000 réservations importées par `load.py` sont toutes « terminées », donc non modifiables. Pour tester les changements de statut, crée d'abord une nouvelle réservation.

---

## 8. La prédiction de durée (machine learning)

### L'idée

Un **modèle** est un programme qui apprend à partir d'exemples. Ici, il apprend sur des millions de trajets passés pour **prédire la durée d'un trajet en minutes** à partir de : l'heure de départ, la zone de départ, la zone d'arrivée et la distance.

### Utiliser la prédiction

```python
import pandas as pd
from predict import predire_duree

exemples = pd.DataFrame([
    {"pickup": "2026-07-15 18:10", "id_location_depart": 162,
     "id_location_arrivee": 236, "distance": 3.2}
])
exemples["duree_predite_min"] = predire_duree(exemples)
```

### Le pipeline d'entraînement (dossier `ml/`)

Lancement, **depuis le dossier `ml/`** (les scripts s'importent entre eux par leur nom) :

```bash
cd ms_api_metier/ml
python run_mlops.py
```

Il enchaîne trois choses :

1. **Entraînement** (`train_ml_models.py`) :
   - extrait les trajets de `yellow_taxi.db` (durée de 1 à 180 min, distance de 0,1 à 80 miles) ;
   - ajoute des variables utiles (même zone ? trajet vers un aéroport ? créneau horaire encodé en cycle) ;
   - sépare les données **dans le temps** : 80 % pour apprendre (train), 20 % pour tester ;
   - entraîne deux modèles, **Random Forest** et **Extra Trees** (100 arbres chacun) ;
   - les compare sur 3 mesures : **MAE** (erreur moyenne en minutes, la plus parlante), **RMSE** et **R²** ;
   - les compare aussi à un modèle « naïf » qui prédit toujours la moyenne (le minimum à battre) ;
   - sauvegarde le meilleur (`model_duree_premier.joblib`) et le second (`model_duree_deuxieme.joblib`).
2. **Évaluation** (`evaluation_model.py`) : teste les modèles sur des données plus récentes (par défaut à partir du 28/07/2026) et vérifie que la MAE reste sous un **seuil** (6 minutes par défaut). Si le seuil est dépassé, le modèle est considéré comme dégradé.
3. **Rapport final** : un fichier JSON qui compare la MAE à l'entraînement et à l'évaluation, avec l'écart (`delta_mae_minutes`).

### Exemple de résultats

| Modèle | MAE | RMSE | R² |
|---|---|---|---|
| Random Forest | ≈ 3,39 min | ≈ 5,26 min | ≈ 0,83 |
| Extra Trees | ≈ 3,55 min | ≈ 5,35 min | ≈ 0,82 |
| Modèle naïf | ≈ 9,01 min | | |

En clair : le modèle se trompe en moyenne d'environ 3,4 minutes, contre 9 minutes pour une simple moyenne.

### Fichiers produits (dans `data/`)

| Fichier | Contenu |
|---|---|
| `models/model_duree_premier.joblib` | Meilleur modèle |
| `models/model_duree_deuxieme.joblib` | Second modèle |
| `evaluation/rapport_entrainement_modeles.json` | Une ligne ajoutée à chaque entraînement |
| `evaluation/evaluation.json` | Une ligne ajoutée à chaque évaluation |
| `evaluation/rapport_final_<date>.json` | Rapport d'un run complet |
| `Matrices_correlation/*.png` | Matrice de corrélation |
| `comparaison_modeles_duree.png` | Graphique des MAE |

Chaque fichier `.joblib` contient le modèle, son nom, la liste des colonnes attendues, les médianes pour combler les valeurs manquantes et ses métriques.

**Outil complémentaire** : `python model_info.py` affiche les informations d'un modèle sauvegardé (nom, métriques, version de scikit-learn, nombre de variables). Il lit `model_duree_extra_trees.joblib`, qui n'est **pas** créé par l'entraînement : il doit déjà exister.

---

## 9. DVC et MLflow : suivre données et expériences

Les données et modèles pèsent plusieurs Go : on ne peut pas les mettre dans Git. Deux outils prennent le relais.

| Outil | Rôle |
|---|---|
| **Git** | Le code, `dvc.yaml`, `dvc.lock`, `params.yaml`, les fichiers `*.dvc` |
| **DVC** | Les gros fichiers (bases, CSV, modèles) + le pipeline reproductible |
| **MLflow** | Le journal des entraînements (paramètres, métriques, graphiques) + registre de modèles |

### Récupérer les données

Configurer le stockage partagé (une fois) puis télécharger :

```bash
dvc remote add -d -f storage ssh://groupe3@xx.xx.xxx.xxx/groupe3
dvc remote modify vm ask_password true
dvc pull
```

⚠️ Ne jamais commiter `.dvc/config.local` (il contient mots de passe et clés).

### Le pipeline DVC (`dvc.yaml`)

```
data/raw → etl → load
              └→ train → evaluate
```

| Étape | Commande | Produit |
|---|---|---|
| `etl` | `python etl.py` | CSV propre + `yellow_taxi.db` |
| `load` | `python load.py` | `frenchcab.db` |
| `train` | `python ml/stage_train.py` | modèles + graphique |
| `evaluate` | `python ml/stage_evaluate.py` | métriques (seuil dans `params.yaml`) |

```bash
dvc repro    # relance uniquement les étapes dont les entrées ont changé
dvc dag      # affiche le graphe
dvc status   # dit ce qui est à jour ou non
```

Les paramètres modifiables (date de début et seuil de MAE) sont dans `params.yaml`.

### Consulter les expériences (MLflow)

Chaque `dvc repro` sur `train` et `evaluate` crée un « run » dans l'expérience `frenchcab-duree-trajet`, avec les tags `git_commit` et `dvc_md5_yellow_taxi_db` pour retrouver le code et les données exacts.

```bash
cd ms_api_metier
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Ouvrir http://127.0.0.1:5000, choisir la vue **Model training** (pas GenAI), l'expérience `frenchcab-duree-trajet`, onglet **Runs**.

### Registre de modèles (à la demande)

```bash
python ml/register_model.py                    # alias "champion"
python ml/register_model.py --modele deuxieme  # alias "challenger"
```

Le modèle est copié dans `mlruns/` (plusieurs Go) : à ne faire que pour promouvoir un modèle.

### Workflow quand on modifie quelque chose

1. Modifier le code, `params.yaml` ou les données.
2. `dvc repro`
3. `git add dvc.lock params.yaml <fichiers modifiés>` (**un par un, jamais `git add .`**).
4. `git commit`
5. `dvc push` **puis** `git push` (sinon les collègues ne retrouvent pas les données).

Nouveau fichier de données brut : `dvc add data/<fichier>` puis `git add data/<fichier>.dvc data/.gitignore`.

### Retrouver un ancien résultat

```bash
git checkout <commit_du_run_mlflow>
dvc checkout      # remet les données correspondantes
```

### Dépannage

| Problème | Solution |
|---|---|
| Pas de runs dans MLflow | Vue « Model training », bonne expérience, interface lancée depuis `ms_api_metier` |
| `dvc pull` échoue | Vérifier `dvc remote list` et `.dvc/config.local` |
| `dvc add` refuse un fichier | Il est ignoré par `.gitignore` : retirer la règle |
| « already exists » sur un remote | Ajouter `-f` : `dvc remote add -d -f ...` |

---

## 10. Docker

Docker permet d'exécuter chaque service dans un conteneur identique partout (ton PC, la VM).

- `docker-compose.yml` (à la racine) décrit les 3 services et leurs réglages ; il lit le fichier `.env` racine.
- Les images sont publiées sur **Docker Hub**, construites automatiquement par la CI à partir de la branche `main`.
- Le dossier de données de l'API est monté en **volume** : sur la VM, `~/frenchcab/api_data` correspond à `/app/data` dans le conteneur. C'est là que vivent bases et modèles, séparément de l'image.

Commandes utiles :

| Commande | Effet |
|---|---|
| `docker compose pull` | Télécharge les dernières images |
| `docker compose build` | Construit les images depuis le code |
| `docker compose up -d` | Démarre les conteneurs en arrière-plan |
| `docker compose ps` | Liste les conteneurs et leur état |

Les dépendances ML (`dvc`, `mlflow`) sont dans un fichier à part, `requirements-ml.txt`, car elles sont inutiles pour l'API et Docker.

---

## 11. Les tests automatiques

À lancer depuis `ms_api_metier` :

```bash
python -m pytest                              # tous les tests
python -m pytest tests/test_load.py -v        # tests de load.py
python -m pytest tests/test_reservations.py -v  # tests des réservations
```

**Principe commun : les tests ne touchent jamais les vraies bases.** Chaque test travaille dans un dossier temporaire avec de mini-données inventées, ce qui le rend rapide et sans risque.

### `test_load.py` : 10 tests (attendu : `10 passed`)

Il vérifie la création des 4 tables, le hachage des mots de passe, les nombres de lignes, les conversions (`Y` → 1, cases vides → valeurs par défaut), les colonnes calculées, les clés étrangères, les liens réservations/trajets et l'absence de doublons si on relance l'import.

### `test_reservations.py` : 22 tests (attendu : `22 passed`)

Il appelle les routes comme le ferait le front et vérifie : création (201), erreurs (400, 404, 422), liste (filtres, ordre, pagination), détail, et changements de statut (chemin normal, sauts interdits 409).

### Comment lire un échec

Le nom du test indique quoi regarder. Par exemple `test_ajouter_...` → fonction `ajouterReservation`, `test_statut_...` → `changerStatut`, `test_relancer_...` → `vider_tables`.

---

## 12. CI/CD : automatiser

- **CI** (intégration continue) : à chaque modification poussée sur GitHub, une chaîne automatique vérifie et construit le projet, puis publie les images Docker depuis `main`.
  ⚠️ **Les tests Python sont actuellement mis en commentaire** dans la CI à cause d'une erreur non résolue (mention « MAJ semaine 3 »). C'est un point à corriger en priorité.
- **CD** (déploiement continu) : un script sur la VM récupère les nouvelles images et redémarre les services à heures fixes (voir ci-dessous).

---

## 13. Déployer sur la VM

### Déploiement du code (automatique)

Sur la VM, une tâche **cron** (planificateur) lance `deploy.sh` à **11h, 15h et 15h20**. Le script fait :

```bash
cd /home/groupe3/frenchcab
docker compose pull      # récupère les nouvelles images
docker compose up -d     # redémarre les services mis à jour
docker compose ps        # vérifie l'état des conteneurs
```

Donc : **merge sur `main` → la CI publie l'image → la VM la récupère au prochain créneau**.

### Déploiement d'un modèle (séparé du code)

Le **code** (`predict.py`) change avec l'image Docker. Le **modèle** (`.joblib`) est un fichier à part, placé dans `api_data/models/`. Les deux sont indépendants.

**Depuis le PC**, après `dvc repro`, la décision de `promote_if_better.py` (qui promeut le modèle seulement s'il est meilleur) et le commit :

```powershell
dvc push -r vm
git push
```

**Sur la VM**, relever l'empreinte `md5:` du modèle dans `ms_api_metier/dvc.lock` :

```bash
grep -A2 "path: data/models/model_duree_premier.joblib" ms_api_metier/dvc.lock | grep md5: | head -1
```

Puis utiliser le script `choisir_modele.sh` :

```bash
./choisir_modele.sh                      # menu : affiche les versions et propose de choisir
./choisir_modele.sh liste                # affiche seulement
./choisir_modele.sh activer <n|md5>      # bascule sans menu
./choisir_modele.sh installer <md5_modele> [<md5_db>] [libelle]   # copie une nouvelle version depuis ~/dvc-storage
```

Comment ça marche : les versions sont rangées dans `api_data/models/versions/` (2 conservées + l'active) et `model_duree_premier.joblib` devient un **lien symbolique** vers la version choisie. Après chaque bascule, le script redémarre `ms_api_metier` et vérifie via `/modele/info` que la bonne version est servie (c'est la même que celle affichée sur la page Angular). Si ce n'est pas le cas, il revient automatiquement en arrière. Prévoir environ **1,4 Go de disque par version**.

Copier les scripts sur la VM (sans installer DVC) :

```bash
scp scripts/choisir_modele.sh scripts/deploy_modele.sh groupe3@<IP>:~/frenchcab/
# puis sur la VM :
sed -i 's/\r$//' *.sh && chmod +x *.sh
```

### Entraînement automatique sur la VM

Un script `mlops` (nommé `mlops.hs` dans le README, sans doute `mlops.sh`) est lancé par cron **toutes les 15 minutes** : il exécute `run_mlops.py` dans le conteneur `ms_api_metier` en cours d'exécution.

### Première installation sur la VM

1. Se connecter à la VM.
2. Dans `frenchcab/api_data`, lancer le script d'initialisation des bases de données.
3. Placer le fichier du modèle entraîné dans `/app/data` (le volume du conteneur).

---

## 14. Règles de travail en équipe

La section « conventions de l'équipe précédente » est vide dans les README d'origine. Voici les règles qui apparaissent **dans** la documentation :

- Ne jamais commiter les fichiers `.env` ni `.dvc/config.local`.
- Ajouter les fichiers à Git **un par un**, jamais `git add .`.
- Toujours faire `dvc push` **avant** `git push`.
- Relancer `etl.py` avant `load.py` après toute nouvelle donnée.
- Lancer les scripts ML depuis le dossier `ml/`.
- Ne jamais écrire les tests sur les vraies bases : utiliser un dossier temporaire.
- Respecter les noms de tests parlants (`test_<route>_<cas>`).
- Les mots de passe sont toujours hachés.
- Ne promouvoir un modèle (registre MLflow, déploiement) que s'il est meilleur.

Si l'équipe précédente avait d'autres conventions (nommage des branches, revue de code, format des messages de commit), il faut les leur demander ou les définir ensemble.

---

## 15. Points à clarifier

En fusionnant les README, j'ai relevé des incohérences ou des trous. À vérifier auprès de l'équipe précédente ou dans le code :

1. **PostgreSQL** : mentionné dans les notes, mais le projet utilise DuckDB et SQLite.
2. **Seuils de nettoyage différents** : `etl.py` retire les courses de plus de 320 miles ou 7 h ; l'entraînement ne garde que 0,1 à 80 miles et 1 à 180 min. Ce n'est pas forcément un bug (deux filtres successifs), mais c'est à savoir.
3. **Fréquence du pipeline MLOps** sur la VM : toutes les 15 minutes, ce qui est très fréquent pour un entraînement lourd.
4. **Chemins différents sur la VM** : `/home/groupe3/frenchcab` pour le déploiement, `/home/ubuntu/frenchcab` pour le script MLOps. Vérifier lequel est le bon.
5. **Nom du script** `mlops.hs` : probablement une faute de frappe pour `mlops.sh`.
6. **Horaires de déploiement** : le README principal parle de 11h et 15h, la doc MLOps de 11h, 15h et 15h20.
7. **Tests Python désactivés dans la CI** (voir section 12).
8. **`model_info.py`** lit un fichier (`model_duree_extra_trees.joblib`) que l'entraînement ne produit pas.
9. **Sections vides** dans le README principal : « Problèmes identifiés » et une partie du déploiement.
10. **Adresse IP et accès du stockage DVC** : masqués (`xx.xx.xxx.xxx`), à demander à l'équipe.

---

## 16. Petit lexique

| Terme | Explication simple |
|---|---|
| **API** | Un guichet par lequel des programmes se demandent des informations |
| **Microservice** | Un petit programme spécialisé, qui fait une seule chose |
| **Conteneur / Docker** | Une boîte isolée contenant un programme et tout ce dont il a besoin |
| **Docker Compose** | Outil pour démarrer plusieurs conteneurs ensemble |
| **Docker Hub** | Un site où l'on stocke et partage des images Docker |
| **Gateway** | Le point d'entrée qui redirige les demandes vers le bon service |
| **ETL** | Extraire, Transformer, Charger : nettoyer des données et les ranger |
| **Parquet / CSV** | Deux formats de fichiers de données (parquet est compact, CSV est lisible) |
| **SQLite / DuckDB** | Deux types de bases de données stockées dans un simple fichier |
| **Clé étrangère** | Un lien qui garantit qu'une ligne pointe vers une ligne qui existe |
| **Hachage (sha256)** | Transformer un mot de passe en une empreinte illisible et irréversible |
| **Modèle (ML)** | Un programme qui a appris à partir d'exemples pour faire des prédictions |
| **MAE** | Erreur moyenne : de combien de minutes le modèle se trompe en moyenne |
| **RMSE** | Comme la MAE, mais pénalise davantage les grosses erreurs |
| **R²** | Part de la variation expliquée par le modèle (1 = parfait) |
| **Modèle naïf** | Une prédiction bête (toujours la moyenne) servant de point de comparaison |
| **MLOps** | Les bonnes pratiques pour entraîner, suivre et déployer des modèles |
| **DVC** | « Git pour les gros fichiers de données » |
| **MLflow** | Un cahier de labo automatique qui note chaque entraînement |
| **CI/CD** | Chaîne automatique qui vérifie, construit puis déploie le code |
| **Cron** | Planificateur qui lance une commande à heures fixes |
| **VM** | Machine virtuelle : un serveur loué sur lequel tourne l'application |
| **Swagger (`/docs`)** | Page web qui documente l'API et permet de la tester |
| **pytest / fixture / monkeypatch** | Outil de tests / données préparées pour un test / remplacement temporaire d'un réglage pendant un test |
| **`.env`** | Fichier de réglages et de secrets, jamais partagé dans Git |
| **Lien symbolique** | Un raccourci de fichier qui pointe vers un autre fichier |
