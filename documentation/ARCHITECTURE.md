# Architecture

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

| Service | Rôle | Port | Documentation |
|---|---|---|---|
| `ms_front` | L'interface web que voit l'utilisateur (écrite en Angular) | 80 | [README_FRONT](README_FRONT.md) |
| `gateway` | Le « standard téléphonique » : reçoit les demandes du front et les redirige vers le bon service | 3000 | [README_GATEWAY](README_GATEWAY.md) |
| `ms_api_metier` | Le cerveau : lit les données, gère les réservations, calcule les prédictions | 8000 | [README_API_METIER](README_API_METIER.md) |

La gateway parle à l'API métier à l'adresse interne `http://ms_api_metier:8000` (le nom du conteneur sert d'adresse dans le réseau Docker).

## Organisation du code

Le dépôt GitHub est : `https://github.com/n4ssim-dev/frenchcab.git`

| Dossier | Contenu |
|---|---|
| `ms_front/` | **Frontend** (ce que voit l'utilisateur), en Angular. Il affiche les courses et dialogue avec la gateway |
| `gateway/` | **Backend** : le routage des requêtes |
| `ms_api_metier/` | **Backend** : tout le reste (données, API des réservations, machine learning) |
| `scripts/` | Scripts de déploiement d'un modèle sur la VM (voir [README_MLOPS](README_MLOPS.md#9-deployer-un-modele-sur-la-vm)) |
| `docker-compose.yml` | Description des 3 services (voir [INSTALLATION](INSTALLATION.md#docker)) |
