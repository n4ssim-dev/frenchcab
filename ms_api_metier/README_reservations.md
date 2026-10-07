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