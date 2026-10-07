# FrenchCab

FrenchCab est une application de consultation et d'exploitation des données Yellow Taxi Trip Records publiées par la New York City Taxi & Limousine Commission (TLC).

Ce projet constitue la première itération de l'application destinée à exploiter des données réelles de transport urbain. Cette première version permet d'importer des courses de taxi, de les stocker dans une base de données relationnelle, de les exposer via une API et de les consulter depuis une interface web.

L'architecture et les procédures ont été volontairement pensées pour permettre à une autre équipe de récupérer, comprendre, tester et déployer le projet sans dépendre des connaissances de l'équipe qui l'a développé.

# Fonctionnalités
La version actuelle permet :
- un import des données Yellow Taxi Trip Records
- une transformation et un nettoyage des données nécessaires
- le stockage dans une base de données relationnelle
- la consultation d'une ou des courses de taxi ainsi que la pagination des résultats sur une interface web
- de réaliser des tests automatisés
- la conteneurisation Docker du front, de la gateway et du microservice python
- un pipeline CI/CD

L'application a été déployée sur une VM et un accès HTTPS à l'application et l'API a été réalisé

# Architecture
Le projet est organisé autour de plusieurs services conteneurisés.

                         Utilisateur
                              |
                              v
                       +--------------+
                       |   ms_front   |
                       | Interface    |
                       |    Web       |
                       +------+-------+
                              |
                              v
                       +--------------+
                       |   gateway    |
                       | API Gateway  |
                       +------+-------+
                              |
                              v
                    +-------------------+
                    |   ms_api_metier   |
                    |    API métier     |
                    |   Base de données |
                    |   relationnelle   |
                    +---------+---------+

|Service|Rôle|Port|
|---|---|---|
|ms_front|Interface web|80|
|gateway|Point d'entrée API / routage|3000|
|ms_api_metier|	API métier|8000|


La **gateway** communique avec l'API métier via :
```
http://ms_api_metier:8000
```

# Prérequis
Pour lancer le projet localement, les éléments suivants sont nécessaires :
```
    Docker
    Docker Compose
    Git
    un compte Docker Hub avec accès aux images du projet
```

# Installation
Cloner le dépôt :
```
https://github.com/n4ssim-dev/frenchcab.git
```

Se placer dans le projet :
```
cd frenchcab
```

Créer les fichier .env à partir de chaque modèle.
- Le fichier .env situé à la racine du projet est utilisé par Docker Compose pour remplacer les variables présentes dans docker-compose.yml.
- Le fichier ```gateway/.env``` contient les variables d'environnement nécessaires au conteneur gateway.

Les fichiers contenant des informations sensibles ne doivent pas être commités dans Git.

# Lancement avec docker
## Récupérer les images Docker
Les services utilisent des images Docker publiées sur Docker Hub.

Pour récupérer les dernières versions :
```
docker compose pull
```

Puis :
```
docker compose up -d
```
## Construire les images docker et démarrer les conteneurs
Pour construire les images docker depuis le répo git : 
```
docker compose build
```
Puis :
```
docker compose up -d
```

# Services 
## Ms_front
L'interface web a été codé en Angular. Elle permet de consulter les courses présentes dans la base de données

## Gateway
Les principales routes de l'API sont :
|Méthode|Route|Description|
|---|---|---|
|GET|```/courses```|Liste toutes les courses de taxi|
|GET|```/courses/:id```|Consulte les détails d'une course|

## MS_api_metier
MS_api_metier permet d'importer les données provenant des Yellow Taxi Trip Records publiées par la New York City Taxi & Limousine Commission :
```
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
```


## Commandes à executer
```
python3 -m venv .venv
. .venv/Scripts/activate 
pip install -r requirements.txt
```

## Téléchargement des fichiers data

```
Executer le fichier dlFichiers.py présent dans le dossier ms_api_metier pour télécharger le fichier data utile et le convertir en csv. Un test vérifie la présence de fichiers générés.
```

## Traitement et chargement des données
```
Executer le fichier etl.py présent dans le dossier ms_api_metier pour traiter les données et les envoyer vers yellow_taxi.db présent dans ms_api_metier/data.
Traitement des incohérences : une course au dela de 320 miles sera supprimée, au dela de 7h également

```
## Composition de yellow_taxi.db
```
Base yellow_taxi.db (DuckDb) est composée de 2 tables, yellowtripdata comprenant toutes les courses et taxi_zones permettant de localiser les zones de prise en charge et de dépose des clients
```

## Entrainement modèle
```
Executer le fichier train.py présent dans ms_api_metier pour lancer le ML en RandomForest (cela va prendre plusieurs minutes)
```
## Prédictions
```
Le fichier predict.py présent dans ms_api_metier permet d'obtenir des prédictions via la fonction predire_duree()

Utilisation : 

exemples = pd.DataFrame([
        {"pickup": "2026-07-15 18:10", "id_location_depart": 162,
         "id_location_arrivee": 236, "distance": 3.2} ])

exemples["duree_predite_min"] = predire_duree(exemples)

```

## Pour lancer les tests

Depuis le repertoire ms_api_metier:

```
python -m pytest
```

# CI/CD
## CI

## CD
Une vérification des images docker a été programmée à 11h et à 15h. A ces horaires, le script suivant est executé sur la machine virtuelle : 
```
    #!/bin/bash

    set -e

    echo "=== Déploiement FrenchCab ==="

    cd /home/groupe3/frenchcab

    echo "=== Récupération des nouvelles images ==="
    docker compose pull

    echo "=== Redémarrage des services ==="
    docker compose up -d

    echo "=== Vérification des conteneurs ==="
    docker compose ps

    echo "=== Déploiement terminé ==="
```