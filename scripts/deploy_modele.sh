#!/usr/bin/env bash
# Conserve pour compatibilite : equivalent de "choisir_modele.sh installer ...".
# Usage : ./deploy_modele.sh <md5_modele> [<md5_yellow_taxi_db>] [libelle]
exec "$(dirname "$0")/choisir_modele.sh" installer "$@"
