#!/usr/bin/env bash
# A LANCER SUR LA VM. Installe dans api_data/ le modele (et optionnellement la
# base) d'un commit donne, depuis le remote DVC local (~/dvc-storage), puis
# redemarre l'API. Aucune installation de DVC n'est necessaire sur la VM.
#
# Usage :
#   ./deploy_modele.sh <md5_modele> [<md5_yellow_taxi_db>]
#
# Les md5 se lisent dans ms_api_metier/dvc.lock du commit a deployer :
#   - modele : ligne "md5:" sous  path: data/models/model_duree_premier.joblib
#   - base   : ligne "md5:" sous  path: data/yellow_taxi.db  (stage etl)
set -euo pipefail

MD5_MODELE="${1:-}"
MD5_BASE="${2:-}"
STOCKAGE="${DVC_STORAGE:-$HOME/dvc-storage}"
PROJET="${FRENCHCAB_DIR:-$HOME/frenchcab}"
DATA="$PROJET/api_data"

valide_md5() { [[ "$1" =~ ^[0-9a-f]{32}$ ]]; }
if ! valide_md5 "$MD5_MODELE"; then
  echo "Usage : $0 <md5_modele> [<md5_yellow_taxi_db>]" >&2
  exit 1
fi
if [ -n "$MD5_BASE" ] && ! valide_md5 "$MD5_BASE"; then
  echo "md5 de la base invalide" >&2
  exit 1
fi

installer() {
  local md5="$1" cible="$2"
  local source="$STOCKAGE/files/md5/${md5:0:2}/${md5:2}"
  if [ ! -f "$source" ]; then
    echo "ERREUR : introuvable dans le remote DVC : $source" >&2
    echo "         (dvc push -r vm fait depuis le PC ?)" >&2
    exit 1
  fi
  local taille dispo reel
  taille=$(stat -c %s "$source")
  dispo=$(df --output=avail -B1 "$(dirname "$cible")" | tail -1 | tr -d ' ')
  if [ "$dispo" -lt $((taille + 500000000)) ]; then
    echo "ERREUR : espace disque insuffisant pour $(basename "$cible")" >&2
    exit 1
  fi
  echo "Copie de $(basename "$cible") ($((taille / 1048576)) Mo)..."
  cp "$source" "$cible.tmp"
  reel=$(md5sum "$cible.tmp" | awk '{print $1}')
  if [ "$reel" != "$md5" ]; then
    rm -f "$cible.tmp"
    echo "ERREUR : empreinte incorrecte (attendu $md5, obtenu $reel)" >&2
    exit 1
  fi
  if [ -f "$cible" ]; then mv -f "$cible" "$cible.prev"; fi
  mv -f "$cible.tmp" "$cible"
  echo "Installe : $cible (md5 $md5)"
}

installer "$MD5_MODELE" "$DATA/models/model_duree_premier.joblib"
if [ -n "$MD5_BASE" ]; then
  installer "$MD5_BASE" "$DATA/yellow_taxi.db"
fi

cd "$PROJET"
echo "--- Fichier de modele attendu par l'image de l'API :"
docker compose exec -T ms_api_metier grep -n "MODEL_PATH =" /app/predict.py || true

echo "--- Redemarrage de l'API"
docker compose restart ms_api_metier
echo -n "Attente de l'API (chargement du modele : jusqu'a 2 minutes) "
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null http://localhost:8000/docs; then
    echo
    echo "API OK. Modele installe : model_duree_premier.joblib md5=$MD5_MODELE"
    echo "Si la ligne MODEL_PATH ci-dessus ne cite pas model_duree_premier.joblib,"
    echo "l'image de l'API n'utilise pas encore ce fichier (voir README, section 9)."
    exit 0
  fi
  echo -n "."
  sleep 4
done
echo
echo "ERREUR : l'API ne repond pas. Voir : docker compose logs ms_api_metier" >&2
echo "Retour arriere : mv $DATA/models/model_duree_premier.joblib.prev $DATA/models/model_duree_premier.joblib" >&2
exit 1
