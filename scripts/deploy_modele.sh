#!/usr/bin/env bash
# Deploie le modele du commit courant : git pull, dvc pull, verification
# de l'empreinte, redemarrage de l'API et controle de sante.
#
# Usage (depuis n'importe ou dans le depot) :
#   ./scripts/deploy_modele.sh                # branche courante
#   ./scripts/deploy_modele.sh dev            # bascule sur la branche dev
#
# Variable optionnelle :
#   DVC_REMOTE=vm-local ./scripts/deploy_modele.sh
#     (utile sur la VM : remote local au lieu de passer par SSH)
set -euo pipefail

BRANCHE="${1:-}"
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE"

MODELE="ms_api_metier/data/models/model_duree_premier.joblib"
SERVICE="ms_api_metier"
URL_SANTE="http://localhost:8000/docs"

echo "==> 1/5 Etat du depot"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "ERREUR : modifications locales non commitees, abandon." >&2
  git status --short --untracked-files=no >&2
  exit 1
fi

echo "==> 2/5 git pull"
if [ -n "$BRANCHE" ]; then
  git fetch origin
  git checkout "$BRANCHE"
fi
git pull --ff-only
echo "Commit courant : $(git rev-parse --short HEAD) ($(git rev-parse --abbrev-ref HEAD))"

echo "==> 3/5 dvc pull (un mot de passe SSH peut etre demande)"
if [ -n "${DVC_REMOTE:-}" ]; then
  dvc pull -r "$DVC_REMOTE"
else
  dvc pull
fi

echo "==> 4/5 Verification de l'empreinte du modele"
attendu="$(grep -A3 "path: data/models/model_duree_premier.joblib" ms_api_metier/dvc.lock \
  | grep -m1 'md5:' | awk '{print $2}' || true)"
if [ -z "$attendu" ]; then
  echo "ERREUR : empreinte du modele introuvable dans dvc.lock." >&2
  exit 1
fi
if [ ! -f "$MODELE" ]; then
  echo "ERREUR : $MODELE absent apres dvc pull." >&2
  exit 1
fi
reel="$(md5sum "$MODELE" | awk '{print $1}')"
if [ "$attendu" != "$reel" ]; then
  echo "ERREUR : le fichier ne correspond pas au commit." >&2
  echo "  attendu (dvc.lock) : $attendu" >&2
  echo "  reel (fichier)     : $reel" >&2
  exit 1
fi
echo "Empreinte OK : $reel"

echo "==> 5/5 Redemarrage de l'API"
docker compose restart "$SERVICE"
echo -n "Attente de l'API (le chargement du modele peut prendre une minute) "
for _ in $(seq 1 30); do
  if curl -fsS -o /dev/null "$URL_SANTE"; then
    echo
    echo "API OK : $URL_SANTE"
    echo "Modele en service : $(basename "$MODELE") md5=$reel"
    exit 0
  fi
  echo -n "."
  sleep 4
done
echo
echo "ERREUR : l'API ne repond pas apres 2 minutes. Voir : docker compose logs $SERVICE" >&2
exit 1
