# CI/CD et déploiement sur la VM

## CI/CD : automatiser

- **CI** (intégration continue) : à chaque modification poussée sur GitHub, une chaîne automatique vérifie et construit le projet, puis publie les images Docker depuis `main`.
  ⚠️ **Les tests Python sont actuellement mis en commentaire** dans la CI à cause d'une erreur non résolue (mention « MAJ semaine 3 »). C'est un point à corriger en priorité.
- **CD** (déploiement continu) : un script sur la VM récupère les nouvelles images et redémarre les services à heures fixes (voir ci-dessous).

## Déploiement du code (automatique)

Sur la VM, une tâche **cron** (planificateur) lance `deploy.sh` à **11h et 15h**. Le script fait :

```bash
cd /home/groupe3/frenchcab
docker compose pull      # récupère les nouvelles images
docker image prune -f    # nettoie des images inutilisées
docker compose up -d     # redémarre les services mis à jour
docker compose ps        # vérifie l'état des conteneurs
```

Donc : **merge sur `main` → la CI publie l'image → la VM la récupère au prochain créneau**.

## Déploiement d'un modèle (séparé du code)

Le **code** (`predict.py`) change avec l'image Docker. Le **modèle** (`.joblib`) est un fichier à part, placé dans `api_data/models/`. Les deux sont indépendants.

La procédure (script `choisir_modele.sh`, gestion des versions, retour arrière automatique) est décrite dans [README_MLOPS](README_MLOPS.md#9-deployer-un-modele-sur-la-vm).

## Entraînement automatique sur la VM

Un script `mlops` est lancé par cron **toutes les 15 minutes** : il exécute `run_mlops.py` dans le conteneur `ms_api_metier` en cours d'exécution.

## Première installation sur la VM

1. Se connecter à la VM.
2. Dans `frenchcab/api_data`, lancer le script d'initialisation des bases de données.
3. Placer le fichier du modèle entraîné dans `/app/data` (le volume du conteneur).

## Accéder à l'application sur la VM

Le pare-feu de la VM ne laisse passer que le SSH : voir [README_FRONT](README_FRONT.md#accéder-à-frenchcab-sur-la-vm--pare-feu-et-tunnel-ssh) pour y accéder avec un tunnel SSH.
