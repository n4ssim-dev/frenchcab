# Installer et lancer le projet

## Prérequis

- Docker et Docker Compose
- Git
- Un compte Docker Hub avec accès aux images du projet
- Pour travailler sur la partie Python en local : Python 3 (voir [README_API_METIER](README_API_METIER.md#environnement-python))

## Installation

```bash
git clone https://github.com/n4ssim-dev/frenchcab.git
cd frenchcab
```

Puis créer les fichiers **`.env`** à partir des modèles fournis :

- le `.env` **à la racine** sert à Docker Compose (il remplit les variables de `docker-compose.yml`) ;
- le `gateway/.env` contient les variables du conteneur gateway.

⚠️ Ces fichiers contiennent des informations sensibles : **ne jamais les commiter dans Git**.

## Lancer avec les images publiées sur Docker Hub

`docker-compose.hub.yml` utilise uniquement les images `<DOCKERHUB_USERNAME>/frenchcab:<service>` publiées par la CI, sans rien construire en local :

```bash
docker compose -f docker-compose.hub.yml pull    # récupère les dernières images
docker compose -f docker-compose.hub.yml up -d   # démarre les conteneurs en arrière-plan
```

## Ou construire les images soi-même

`docker-compose.yml` (et `docker-compose.override.yml`, chargé automatiquement, qui monte le code source dans les conteneurs pour le développement) construit les images depuis le code :

```bash
docker compose build
docker compose up -d
```

## Docker

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
