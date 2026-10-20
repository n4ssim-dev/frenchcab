#!/usr/bin/env bash
# Gestion des versions du modele de duree sur la VM : affiche les 2 dernieres
# versions et permet de choisir laquelle l'API utilise.
#
#   ./choisir_modele.sh                    liste les versions et propose de choisir
#   ./choisir_modele.sh liste              affiche seulement
#   ./choisir_modele.sh activer <n|md5>    active une version sans question
#                                          (numero de la liste ou debut du md5)
#   ./choisir_modele.sh installer <md5_modele> [<md5_yellow_taxi_db>] [libelle]
#                                          ajoute une version depuis le remote DVC
#
# Organisation de api_data/models/ (monte dans le conteneur sur /app/data/models) :
#   versions/<md5>.joblib + <md5>.info   les versions disponibles
#   model_duree_premier.joblib           lien vers la version active (lu par l'API)
set -euo pipefail

PROJET="${FRENCHCAB_DIR:-$HOME/frenchcab}"
STOCKAGE="${DVC_STORAGE:-$HOME/dvc-storage}"
DATA="$PROJET/api_data"
MODELES="$DATA/models"
VERSIONS="$MODELES/versions"
ACTIF="$MODELES/model_duree_premier.joblib"
GARDER="${GARDER_VERSIONS:-2}"
URL_API="${URL_API:-http://localhost:8000}"

erreur() { echo "ERREUR : $*" >&2; exit 1; }
valide_md5() { [[ "$1" =~ ^[0-9a-f]{32}$ ]]; }

# ---------- metadonnees ----------
lire_info() { # $1 md5, $2 cle
  grep -m1 "^$2=" "$VERSIONS/$1.info" 2>/dev/null | cut -d= -f2- || true
}
ecrire_info() { # $1 md5, $2 date (epoch), $3 libelle
  printf 'installe_le=%s\nlibelle=%s\n' "$2" "$3" > "$VERSIONS/$1.info"
}
md5_actif() {
  if [ -L "$ACTIF" ]; then basename "$(readlink "$ACTIF")" .joblib; fi
}

# remplit MD5S, EPOCHS, LIBELLES : du plus recent au plus ancien
lister() {
  MD5S=(); EPOCHS=(); LIBELLES=()
  local f m e lignes
  lignes=$(for f in "$VERSIONS"/*.joblib; do
      [ -e "$f" ] || continue
      m=$(basename "$f" .joblib)
      e=$(lire_info "$m" installe_le)
      [ -n "$e" ] || e=$(stat -c %Y "$f")
      echo "$e $m"
    done | sort -rn)
  while read -r e m; do
    [ -n "$m" ] || continue
    MD5S+=("$m"); EPOCHS+=("$e"); LIBELLES+=("$(lire_info "$m" libelle)")
  done <<< "$lignes"
}

# ---------- migration de l'ancien format (fichiers simples + .prev) ----------
migrer_existant() {
  mkdir -p "$VERSIONS"
  local f m e libelle
  for f in "$ACTIF" "$ACTIF.prev"; do
    if [ -f "$f" ] && [ ! -L "$f" ]; then
      m=$(md5sum "$f" | awk '{print $1}')
      e=$(stat -c %Y "$f")
      echo "Migration de $(basename "$f") vers versions/${m:0:8}..."
      if [ -f "$VERSIONS/$m.joblib" ]; then rm -f "$f"; else mv "$f" "$VERSIONS/$m.joblib"; fi
      if [ "$f" = "$ACTIF" ]; then libelle="version en service avant migration"; else libelle="version precedente"; fi
      [ -f "$VERSIONS/$m.info" ] || ecrire_info "$m" "$e" "$libelle"
      if [ "$f" = "$ACTIF" ]; then poser_lien "$m"; fi
    fi
  done
}

poser_lien() { # $1 md5 : bascule le lien de maniere atomique
  ln -sfn "versions/$1.joblib" "$ACTIF.lien"
  mv -Tf "$ACTIF.lien" "$ACTIF"
}

# ---------- affichage ----------
info_api() {
  curl -fsS --max-time 10 "$URL_API/modele/info" 2>/dev/null | python3 -c '
import json, sys
d = json.load(sys.stdin)
m = d.get("metriques", {}).get("mae_minutes")
print("%s, version %s%s" % (d["nom_modele"], d["version"], (", MAE %s min" % m) if m is not None else ""))
' 2>/dev/null || echo "non disponible (API arretee, modele en chargement ou image sans /modele/info)"
}

afficher() {
  lister
  local n=${#MD5S[@]} actif i f taille
  echo
  echo "Modele servi actuellement par l'API : $(info_api)"
  if [ "$n" -eq 0 ]; then
    echo "Aucune version installee. Ajouter : $0 installer <md5_modele>"
    return 1
  fi
  actif=$(md5_actif)
  echo
  echo "Versions disponibles :"
  for ((i = 0; i < n; i++)); do
    f="$VERSIONS/${MD5S[$i]}.joblib"
    taille=$(awk -v t="$(stat -c %s "$f")" 'BEGIN { printf "%.1f", t / 1073741824 }')
    printf "  %d) %s   installee le %s   %s Go" "$((i + 1))" "${MD5S[$i]:0:8}" \
      "$(date -d "@${EPOCHS[$i]}" '+%d/%m/%Y %H:%M')" "$taille"
    [ -z "${LIBELLES[$i]}" ] || printf "   [%s]" "${LIBELLES[$i]}"
    [ "${MD5S[$i]}" != "$actif" ] || printf "   <== ACTIVE"
    printf "\n"
  done
}

# ---------- redemarrage et verification ----------
redemarrer() {
  ( cd "$PROJET" && docker compose restart ms_api_metier ) > /dev/null
  echo -n "Redemarrage de l'API "
  local _
  for _ in $(seq 1 30); do
    if curl -fsS -o /dev/null --max-time 5 "$URL_API/health" 2>/dev/null; then
      echo
      return 0
    fi
    echo -n "."
    sleep 4
  done
  echo
  return 1
}

# 0 = bonne version servie, 2 = /modele/info absent de l'image, 1 = echec
verifier() { # $1 md5 attendu
  local corps code ver
  corps=$(mktemp)
  echo "Verification : chargement du modele par l'API (peut prendre une minute)..."
  code=$(curl -sS --max-time 170 -o "$corps" -w '%{http_code}' "$URL_API/modele/info" 2>/dev/null || echo 000)
  if [ "$code" = "404" ]; then rm -f "$corps"; return 2; fi
  if [ "$code" != "200" ]; then rm -f "$corps"; return 1; fi
  ver=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("version", ""))' "$corps" 2>/dev/null || true)
  rm -f "$corps"
  [ "$ver" = "${1:0:8}" ]
}

# ---------- changement de version ----------
resoudre() { # $1 numero de la liste ou debut de md5 -> md5 complet
  lister
  local spec="$1" i
  if [[ "$spec" =~ ^[0-9]{1,2}$ ]] && [ "$spec" -ge 1 ] && [ "$spec" -le "${#MD5S[@]}" ]; then
    echo "${MD5S[$((spec - 1))]}"
    return 0
  fi
  for i in "${!MD5S[@]}"; do
    case "${MD5S[$i]}" in "$spec"*) echo "${MD5S[$i]}"; return 0 ;; esac
  done
  return 1
}

activer() { # $1 numero ou debut de md5
  local md5 actif rc
  md5=$(resoudre "$1") || erreur "version introuvable : $1 (voir : $0 liste)"
  actif=$(md5_actif)
  if [ "$actif" = "$md5" ]; then
    echo "La version ${md5:0:8} est deja active."
    return 0
  fi
  poser_lien "$md5"
  echo "Version ${md5:0:8} activee, redemarrage de l'API..."
  if redemarrer; then
    verifier "$md5" && rc=0 || rc=$?
  else
    rc=1
  fi
  case "$rc" in
    0) echo "OK : l'API sert la version ${md5:0:8}."
       echo "Modele servi : $(info_api)" ;;
    2) echo "OK : API redemarree. Verification impossible (l'image n'a pas encore /modele/info)." ;;
    *) echo "ECHEC : l'API ne sert pas la version attendue." >&2
       if [ -n "$actif" ]; then
         echo "Retour a la version ${actif:0:8}..." >&2
         poser_lien "$actif"
         redemarrer || true
       fi
       exit 1 ;;
  esac
}

choisir() {
  migrer_existant
  afficher || return 1
  [ -t 0 ] || return 0
  local reponse confirmation md5
  echo
  read -r -p "Numero de la version a utiliser (Entree pour annuler) : " reponse
  [ -n "$reponse" ] || { echo "Aucun changement."; return 0; }
  md5=$(resoudre "$reponse") || erreur "choix invalide : $reponse"
  read -r -p "Basculer l'API sur la version ${md5:0:8} ? (le service redemarre, environ 1 minute) [o/N] " confirmation
  case "$confirmation" in
    o | O | oui | OUI) activer "$md5" ;;
    *) echo "Aucun changement." ;;
  esac
}

# ---------- installation d'une version depuis le remote DVC ----------
copier_remote() { # $1 md5, $2 fichier cible
  local md5="$1" cible="$2" source taille dispo reel
  source="$STOCKAGE/files/md5/${md5:0:2}/${md5:2}"
  [ -f "$source" ] || erreur "introuvable dans le remote DVC : $source (dvc push -r vm fait depuis le PC ?)"
  taille=$(stat -c %s "$source")
  dispo=$(df --output=avail -B1 "$(dirname "$cible")" | tail -1 | tr -d ' ')
  [ "$dispo" -ge $((taille + 500000000)) ] || erreur "espace disque insuffisant pour $(basename "$cible")"
  echo "Copie de $(basename "$cible") ($((taille / 1048576)) Mo)..."
  cp "$source" "$cible.tmp"
  reel=$(md5sum "$cible.tmp" | awk '{print $1}')
  [ "$reel" = "$md5" ] || { rm -f "$cible.tmp"; erreur "empreinte incorrecte (attendu $md5, obtenu $reel)"; }
  mv -f "$cible.tmp" "$cible"
}

elaguer() { # $1 = places a liberer : garde (GARDER - $1) versions recentes + la version active
  local garde=$((GARDER - ${1:-0})) actif i
  lister
  actif=$(md5_actif)
  for i in "${!MD5S[@]}"; do
    [ "${MD5S[$i]}" = "$actif" ] && continue
    [ "$i" -lt "$garde" ] && continue
    echo "Suppression de l'ancienne version ${MD5S[$i]:0:8}"
    rm -f "$VERSIONS/${MD5S[$i]}.joblib" "$VERSIONS/${MD5S[$i]}.info"
  done
}

installer() {
  local md5="${1:-}" md5base="${2:-}" libelle="${3:-}"
  valide_md5 "$md5" || erreur "usage : $0 installer <md5_modele> [<md5_yellow_taxi_db>] [libelle]"
  if [ -n "$md5base" ]; then valide_md5 "$md5base" || erreur "md5 de la base invalide"; fi
  migrer_existant
  if [ -f "$VERSIONS/$md5.joblib" ]; then
    echo "La version ${md5:0:8} est deja installee."
  else
    elaguer 1
    copier_remote "$md5" "$VERSIONS/$md5.joblib"
    ecrire_info "$md5" "$(date +%s)" "$libelle"
  fi
  if [ -n "$md5base" ]; then
    copier_remote "$md5base" "$DATA/yellow_taxi.db.nouveau"
    if [ -f "$DATA/yellow_taxi.db" ]; then mv -f "$DATA/yellow_taxi.db" "$DATA/yellow_taxi.db.prev"; fi
    mv -f "$DATA/yellow_taxi.db.nouveau" "$DATA/yellow_taxi.db"
    echo "Base yellow_taxi.db mise a jour (ancienne : yellow_taxi.db.prev, prise en compte au prochain redemarrage)."
  fi
  echo "Version ${md5:0:8} installee. Pour l'activer, lancer : $0"
}

# ---------- point d'entree ----------
commande="${1:-choisir}"
shift || true
case "$commande" in
  choisir) choisir ;;
  liste) migrer_existant; afficher ;;
  activer) [ $# -ge 1 ] || erreur "usage : $0 activer <numero|debut_md5>"; migrer_existant; activer "$1" ;;
  installer) installer "$@" ;;
  *) erreur "commande inconnue : $commande (choisir | liste | activer | installer)" ;;
esac
