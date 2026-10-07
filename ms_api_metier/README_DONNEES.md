# load.py

Script qui crée la base SQLite `frenchcab.db` et la remplit avec les données des taxis de New York 



Lancer le script

```bash
cd ms\_api\_metier
python load.py
```



Le script peut être relancé autant de fois que nécessaire, il vide les tables avant de les remplir

## Fichiers utilisés

|Fichier|Rôle|
|-|-|
|`data/raw/taxi\_zone\_lookup.csv`|Liste des 265 zones de New York|
|`data/yellow\_tripdata\_2026-07\_propre.csv`|Trajets nettoyés par `etl.py`|
|`data/frenchcab.db`|Base créée par le script|

Le fichier `yellow\_tripdata\_2026-07\_propre.csv` est produit par `etl.py`, il faut donc lancer `etl.py` avant `load.py`

## Les tables

```
clients ──< reservations >── trajets
              │    │            │
              └────┴── lieux ───┘
```

|Table|Contenu|Remplie avec|
|-|-|-|
|`lieux`|Zones|`taxi\_zone\_lookup.csv`|
|`clients`|Clients|15 clients d'exemple écrits dans le script|
|`reservations`|Réservations des clients|Générées à partir de 50 000 trajets tirés au hasard|
|`trajets`|Courses de taxi|`yellow\_tripdata\_2026-07\_propre.csv`|



```
trajets.uid\_reservation  ->  reservations.uid\_client  ->  clients
```

## Pourquoi des clients d'exemple

Les données des taxis de New York ne contiennent aucune information sur les clients

Pour pouvoir calculer des statistiques par client, le script crée 15 clients fictifs et les rattache à une partie des trajets

Chaque client a un poids qui représente sa fréquence d'utilisation

|uid\_client|Nom|Poids|
|-|-|-|
|1|Alice Martin|10|
|2|Bruno Lefevre|8|
|3|Chloe Bernard|6|



Un client de poids 10 fait environ 10 fois plus de trajets qu'un client de poids 1, ce qui donne des statistiques différentes d'un client à l'autre

Les mots de passe sont enregistrés hachés en sha256, jamais en clair

## 

## Paramètres

En haut du script

|Variable|Valeur|Rôle|
|-|-|-|
|`NB\_TRAJETS\_AVEC\_CLIENT`|50 000|Nombre de trajets rattachés à un client|
|`GRAINE`|42|Graine du tirage au hasard, même graine donne mêmes résultats|
|`STATUT\_TERMINEE`|2|Statut donné aux réservations générées|

## 

## Les fonctions

|Fonction|Rôle|
|-|-|
|`creer\_base\_si\_inexistante()`|Crée les tables si elles n'existent pas|
|`vider\_tables(conn)`|Vide les tables (enfants d'abord à cause des clés étrangères)|
|`importer\_lieux(conn)`|Importe les zones|
|`importer\_clients(conn)`|Ajoute les clients d'exemple|
|`preparer\_trajets(ids\_lieux)`|Lit et nettoie le CSV des trajets|
|`creer\_reservations(conn, df)`|Crée les réservations et les relie aux trajets|
|`importer\_trajets(conn, df)`|Écrit les trajets dans la base|
|`importer\_donnees()`|Lance toutes les étapes dans l'ordre|
|`hacher(mot\_de\_passe)`|Renvoie l'empreinte sha256 d'un mot de passe|

## Ordre des étapes

1. Création des tables
2. Vidage des tables
3. Import des lieux
4. Import des clients
5. Lecture et préparation des trajets
6. Création des réservations
7. Import des trajets

On remplit toujours les tables parents avant les tables enfants, sinon les clés étrangères refusent l'insertion

## Préparation des trajets

|Problème dans le CSV|Correction|
|-|-|
|Noms de colonnes différents de la table (`PULocationID`)|Renommage (`PU\_locationID`)|
|`store\_and\_fwd\_flag` vaut `Y` ou `N`|Converti en 1 ou 0|
|Cases vides dans `passenger\_count`|Remplacées par 1|
|Cases vides dans `RatecodeID`|Remplacées par 99 (inconnu)|
|Cases vides dans `Airport\_fee` et `congestion\_surcharge`|Remplacées par 0|
|Pas de durée ni d'heure de départ|Calcul de `trip\_duration\_min`, `pickup\_hour`, `pickup\_weekday`|
|Texte `N/A` lu comme case vide par pandas|Lecture avec `keep\_default\_na=False`|
|Zone de départ ou d'arrivée inconnue|Trajet retiré|

## Création des réservations

Pour chacun trajets tirés au hasard

* un client est choisi selon les poids
* la réservation reprend la zone de départ, la zone d'arrivée, la date et l'heure du trajet
* la date de réservation est placée entre 10 minutes et 2 heures avant le départ
* le statut est `2` (terminée)

Les autres trajets n'ont pas de réservation (`uid\_reservation` vide), ce sont des courses prises dans la rue

## Résultat attendu

```
lieux        265 lignes
clients      15 lignes
reservations 50000 lignes
trajets      3527158 lignes
```

## Vérifier les statistiques par client

```bash
python stats\_clients.py
```

Alice Martin doit apparaître en premier avec le plus de trajets et Oceane Petit en dernier




# test_load.py

Tests automatiques du script `load.py`

Emplacement `ms_api_metier/tests/test_load.py`

## Lancer les tests

```bash
cd ms_api_metier
python -m pytest tests/test_load.py -v
```

Résultat attendu `10 passed` en moins d'une seconde

## Principe

Les tests ne touchent jamais la vraie base `frenchcab.db`

- trop lente (3,5 millions de trajets)
- risque de l'abîmer

Chaque test travaille dans un dossier temporaire créé puis effacé par pytest (`tmp_path`), avec un mini CSV de zones et un mini CSV de trajets écrits directement dans le fichier de test

`monkeypatch` remplace pendant le test seulement les chemins de `load.py` (`DB_PATH`, `ZONES_CSV`, `TRAJETS_CSV`) et le nombre de trajets avec client (`NB_TRAJETS_AVEC_CLIENT` passe à 2)

## Les fausses données

4 zones

| locationID | Zone |
|---|---|
| 1 | Newark Airport |
| 2 | Jamaica Bay |
| 3 | Midtown |
| 264 | N/A |

4 trajets

| Ligne | Particularité | Ce qu'elle permet de tester |
|---|---|---|
| 1 | Trajet normal de 30 minutes le 01/07/2026 à 10h | Colonnes calculées |
| 2 | Cases vides et `store_and_fwd_flag` à `Y` | Valeurs par défaut et conversion |
| 3 | Trajet normal | Comptage |
| 4 | Zone d'arrivée 999 qui n'existe pas | Retrait des trajets avec zone inconnue |

## Les fixtures

| Fixture | Rôle |
|---|---|
| `fausse_base` | Écrit les faux CSV, redirige `load.py` vers eux et crée les tables vides |
| `base_remplie` | Lance l'import complet sur la fausse base et ouvre une connexion |

## Les tests

| Test | Ce qui est vérifié |
|---|---|
| `test_creerBase_creeLes4Tables` | Les tables `clients`, `lieux`, `reservations`, `trajets` existent |
| `test_creerBase_deuxFoisSansErreur` | Un deuxième appel ne plante pas et affiche que la base existe déjà |
| `test_hacher_neStockePasEnClair` | Le mot de passe haché est différent du mot de passe, fait 64 caractères et donne toujours le même résultat |
| `test_nombreDeLignes` | 4 lieux, 15 clients, 3 trajets (la ligne avec la zone 999 est retirée), 2 réservations |
| `test_lieux_NAgardeCommeTexte` | La zone 264 garde le texte `N/A` |
| `test_trajets_conversions` | `Y` devient 1, les cases vides deviennent 1, 99 et 0 |
| `test_trajets_colonnesCalculees` | Durée 30 minutes, heure 10, jour 2 (mercredi) |
| `test_clesEtrangeres_ok` | `PRAGMA foreign_key_check` ne trouve aucun lien cassé |
| `test_reservations_lieesAuxTrajets` | Les 2 réservations sont reliées à un trajet et à un client, avec la même zone de départ |
| `test_relancer_pasDeDoublons` | Un deuxième import ne crée pas de doublons |

## En cas d'échec

Le nom du test indique la partie de `load.py` à vérifier

| Test en échec | Fonction à vérifier |
|---|---|
| `test_creerBase_...` | `creer_base_si_inexistante` |
| `test_hacher_...` | `hacher` |
| `test_lieux_...` | `importer_lieux` |
| `test_trajets_...` | `preparer_trajets` ou `importer_trajets` |
| `test_reservations_...` | `creer_reservations` |
| `test_relancer_...` | `vider_tables` |



# Réservations - API  metier

Partie de l'API `ms_api_metier` qui gère les réservations de taxi

- Fichier des routes `routes/reservations.py`
- Base de données SQLite `data/frenchcab.db` (créée / remplie par `load.py`)
- Tests `tests/test_reservations.py`

## Lancer l'API

```bash
cd ms_api_metier
python load.py
uvicorn main:app --reload
```

Documentation interactive sur http://127.0.0.1:8000/docs

## Les statuts d'une réservation

| Code | Nom |
|---|---|
| 0 | en attente |
| 1 | confirmée |
| 2 | terminée |
| 3 | annulée |

Changements de statut autorisés

```
0 en attente ──► 1 confirmée ──► 2 terminée
     │                │
     └────────────────┴──► 3 annulée
```

- Une nouvelle réservation est toujours `en attente`
- On ne peut pas passer directement de `en attente` à `terminée`
- `terminée` et `annulée` sont des statuts finaux, on ne peut plus les changer

## Les routes

| Méthode | Route | Fonction | Rôle |
|---|---|---|---|
| POST | `/reservations` | `ajouterReservation` | Ajouter une réservation |
| GET | `/reservations` | `listerReservations` | Lister les réservations |
| GET | `/reservations/{uid_reservation}` | `detailReservation` | Voir une réservation |
| PATCH | `/reservations/{uid_reservation}/statut` | `changerStatut` | Changer le statut |

---

### 1. Ajouter une réservation

`POST /reservations`

Nom dans Swagger `ajouterReservation_reservations_post`

Body JSON

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

| Champ | Type | Description |
|---|---|---|
| `uid_client` | entier > 0 | Client qui réserve |
| `resa_PU_locationID` | entier > 0 | Zone de départ |
| `resa_DO_locationID` | entier > 0 | Zone d'arrivée |
| `resa_date` | date `AAAA-MM-JJ` | Date de départ |
| `resa_heure` | heure `HH:MM` | Heure de départ |
| `estimation_duree_course` | nombre > 0 | Durée estimée en minutes |

Remplis automatiquement par l'API

- `uid_reservation` numéro créé par la base
- `date_heure_reservation` date et heure du moment de la réservation
- `statut_resa` toujours `0` (en attente)

Réponse `201 Created`

```json
{
  "uid_reservation": 50001,
  "resa_PU_locationID": 132,
  "resa_DO_locationID": 161,
  "resa_date": "2026-12-01",
  "resa_heure": "08:30:00",
  "estimation_duree_course": 45.0,
  "date_heure_reservation": "2026-10-07 14:00:00",
  "statut_resa": 0,
  "uid_client": 1,
  "statut_nom": "en attente"
}
```

Erreurs possibles

| Code | Raison |
|---|---|
| 400 | La date de départ est dans le passé |
| 404 | Client ou zone introuvable |
| 422 | Données mal formées (heure `25:00`, durée négative, champ manquant) |
| 503 | Base absente, lancer `load.py` |

---

### 2. Lister les réservations

`GET /reservations`

Nom dans `listerReservations_reservations_get`


| Paramètre | Défaut | Description |
|---|---|---|
| `limit` | 100 | Nombre de réservations par page (1 à 1000) |
| `offset` | 0 | Nombre de réservations à sauter (pagination) |
| `uid_client` | aucun | Seulement les réservations de ce client |
| `statut` | aucun | Seulement ce statut (0, 1, 2 ou 3) |

Exemples

```
GET /reservations
GET /reservations?uid_client=1
GET /reservations?statut=0
GET /reservations?uid_client=1&statut=0
GET /reservations?limit=10&offset=20
```

Les plus récentes sont en premier

Réponse `200 OK`

```json
{
  "total": 3,
  "limit": 100,
  "offset": 0,
  "reservations": [
    { "uid_reservation": 50003, "uid_client": 1, "statut_resa": 0, "statut_nom": "en attente" },
    { "uid_reservation": 50002, "uid_client": 1, "statut_resa": 1, "statut_nom": "confirmée" }
  ]
}
```

`total` donne le nombre de réservations qui correspondent aux filtres

Erreurs possibles

| Code | Raison |
|---|---|
| 422 | Paramètre invalide (`statut=7`, `limit=5000`) |

---

### 3. Voir une réservation

`GET /reservations/{uid_reservation}`

Nom dans Swagger `detailReservation_reservations__uid_reservation__get`

Exemple

```
GET /reservations/50001
```

Réponse `200 OK` avec la réservation (même format que la réponse de l'ajout)

Erreurs possibles

| Code | Raison |
|---|---|
| 404 | Réservation introuvable |

---

### 4. Changer le statut

`PATCH /reservations/{uid_reservation}/statut`

Nom dans Swagger `changerStatut_reservations__uid_reservation__statut_patch`

Exemple

```
PATCH /reservations/50001/statut
```

Body JSON

```json
{ "statut": 1 }
```

Réponse `200 OK` avec la réservation mise à jour

```json
{
  "uid_reservation": 50001,
  "statut_resa": 1,
  "statut_nom": "confirmée"
}
```

Erreurs possibles

| Code | Raison |
|---|---|
| 404 | Réservation introuvable |
| 409 | Changement interdit (exemple `en attente` vers `terminée`, ou statut final) |
| 422 | Statut invalide (autre que 0, 1, 2, 3) |

---

## Données de test

Clients créés par `load.py`

| uid_client | Nom |
|---|---|
| 1 | Alice Martin |
| 2 | Bruno Lefevre |
| 3 | Chloe Bernard |
| 4 | David Moreau |
| 5 | Emma Laurent |

Quelques zones

| locationID | Zone |
|---|---|
| 1 | Newark Airport |
| 79 | East Village |
| 132 | JFK Airport |
| 138 | LaGuardia Airport |
| 161 | Midtown Center |
| 230 | Times Sq/Theatre District |
| 236 | Upper East Side North |

Script qui ajoute 8 réservations de test par l'API (l'API doit tourner)

```bash
python ajouter_reservations_test.py
```

Les 50 000 réservations importées par `load.py` sont toutes `terminée`, leur statut ne peut plus changer
Pour tester le changement de statut, créer d'abord une nouvelle réservation

## Tests

```bash
cd ms_api_metier
python -m pytest tests/test_reservations.py -v
```




# test_reservations.py

Tests automatiques des routes de réservations (`routes/reservations.py`)

Emplacement `ms_api_metier/tests/test_reservations.py`

## Lancer les tests

```bash
cd ms_api_metier
python -m pytest tests/test_reservations.py -v
```

Résultat attendu `22 passed`

## Principe

Les tests appellent les routes avec `TestClient` de FastAPI, comme le ferait le front, sans lancer de serveur

Ils ne touchent jamais la vraie base `frenchcab.db`

- la fixture crée une base vide dans un dossier temporaire (`tmp_path`)
- `monkeypatch` et `patch` redirigent `load.DB_PATH` et `routes.reservations.DB_PATH` vers cette base pendant le test

## Les données de test

La base temporaire contient

| Table | Contenu |
|---|---|
| `clients` | 1 Alice, 2 Bruno |
| `lieux` | Zones 1 et 2 |
| `reservations` | Vide au départ |

Réservation valide utilisée par la plupart des tests (`RESA`)

```json
{
  "uid_client": 1,
  "resa_PU_locationID": 1,
  "resa_DO_locationID": 2,
  "resa_date": "2099-12-01",
  "resa_heure": "14:30",
  "estimation_duree_course": 25
}
```

La date est en 2099 pour que le test reste valable dans le temps, la route refuse les dates passées

## Les outils du fichier

| Nom | Type | Rôle |
|---|---|---|
| `base` | Fixture | Base vide avec 2 clients et 2 zones |
| `trois_resas` | Fixture | Ajoute 3 réservations (2 pour Alice, 1 pour Bruno, la première confirmée) |
| `ajouter(**changements)` | Fonction | Envoie `RESA` en remplaçant seulement les champs donnés |
| `changer(uid, statut)` | Fonction | Appelle la route de changement de statut |

Exemple `ajouter(uid_client=99)` envoie la réservation valide avec seulement le client changé

## Les tests

### POST /reservations

| Test | Ce qui est vérifié | Code attendu |
|---|---|---|
| `test_ajouter_ok` | Réservation créée, numéro 1, statut en attente, heure au format `14:30:00` | 201 |
| `test_ajouter_heureAvecFuseau` | Une heure envoyée avec fuseau (`14:30:00Z`) ne provoque pas d'erreur 500 | 201 |
| `test_ajouter_enregistreDansLaBase` | La ligne est bien écrite dans la table | 201 |
| `test_ajouter_clientIntrouvable` | Client 99 | 404 |
| `test_ajouter_zoneIntrouvable` | Zone 999 | 404 |
| `test_ajouter_dateDansLePasse` | Date 2020-01-01 | 400 |
| `test_ajouter_donneesInvalides` | Heure `25:00`, durée négative, client 0 | 422 |

### GET /reservations

Ces tests utilisent la fixture `trois_resas`

| Test | Ce qui est vérifié | Résultat attendu |
|---|---|---|
| `test_liste_vide` | Liste sans réservation | total 0 |
| `test_liste_tout_plusRecenteEnPremier` | Ordre de la liste | 3, 2, 1 |
| `test_liste_filtreClient` | Filtre `uid_client` | 2 pour Alice, 1 pour Bruno |
| `test_liste_filtreStatut` | Filtre `statut` | 2 en attente, 1 confirmée |
| `test_liste_deuxFiltres` | Filtres client et statut ensemble | réservation 2 seulement |
| `test_liste_pagination` | `limit=1` et `offset=1` | réservation 2, total toujours 3 |
| `test_liste_parametresInvalides` | `statut=7` et `limit=5000` | 422 |

### GET /reservations/{uid_reservation}

| Test | Ce qui est vérifié | Code attendu |
|---|---|---|
| `test_detail_ok` | Détail d'une réservation existante | 200 |
| `test_detail_introuvable` | Réservation 999 | 404 |

### PATCH /reservations/{uid_reservation}/statut

| Test | Ce qui est vérifié | Code attendu |
|---|---|---|
| `test_statut_cheminNormal` | en attente vers confirmée puis terminée | 200 |
| `test_statut_annulerDepuisAttente` | en attente vers annulée | 200 |
| `test_statut_sautInterdit` | en attente vers terminée directement | 409 |
| `test_statut_finalBloque` | Une réservation annulée ne peut plus changer | 409 |
| `test_statut_introuvable` | Réservation 999 | 404 |
| `test_statut_invalide` | Statut 7 | 422 |

## Rappel des codes HTTP

| Code | Signification |
|---|---|
| 200 | Demande réussie |
| 201 | Réservation créée |
| 400 | Demande refusée (date passée) |
| 404 | Élément introuvable |
| 409 | Changement de statut interdit |
| 422 | Données mal formées, refusées automatiquement par Pydantic |

## En cas d'échec

Le nom du test indique la route et le cas en erreur

| Début du nom | Fonction à vérifier dans `routes/reservations.py` |
|---|---|
| `test_ajouter_` | `ajouterReservation` |
| `test_liste_` | `listerReservations` |
| `test_detail_` | `detailReservation` |
| `test_statut_` | `changerStatut` |
