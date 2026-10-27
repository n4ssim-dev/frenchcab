# Gateway

Le « standard téléphonique » de FrenchCab : la gateway reçoit les demandes du front (port **3000**) et les redirige vers l'API métier, à l'adresse interne `http://ms_api_metier:8000` (le nom du conteneur sert d'adresse dans le réseau Docker).

Ses variables d'environnement sont dans `gateway/.env` (voir [INSTALLATION](INSTALLATION.md#installation)).

## Routes principales

| Méthode | Route | Description |
|---|---|---|
| GET | `/courses` | Liste toutes les courses de taxi |
| GET | `/courses/:id` | Détails d'une course |
