# RAPPORT de la recette de la S4
Tout semble fonctionner sur le Front, cependant en suivant le GUIDE_FRENCHCAB nous avons rencontré plusieurs échecs doncumenté ci-dessous.

Il y a un fichier `PRISE EN MAIN PROJET par G1.md` qui semble n'être d'aucune utilité.

Deux Readme sont présent à la base et il est difficile de savoir lequel suivre pour l'installation : 
- `README.md`
- `GUIDE_FRENCHCAB.md`

Nous avons suivit le fichier `GUIDE_FRENCHCAB.md`

## GUIDE_FRENCHCAB.md

### 4. Les données et les bases 
1. Cette note est toujours présente mais est-ce qu'elle est toujours d'actualité (ligne 131)? : *> Les notes de départ mentionnent aussi une « base analytique PostgreSQL ». Elle n'apparaît dans aucun autre README : voir [Points à clarifier]
(#15-points-à-clarifier).*

### 5. Installer et lancer le projet
2. Dans le .env.exemple du ms_api_metier il n'y a rien

### 9. DVC et MLflow : suivre données et expèriences
1. Il faut installer dvc dans un premier temps:
```
pip install dvc
```
Après l'exécution des commandes :
en mettant les bons identifiants
```powershell
dvc remote add -d -f storage ssh://groupe3@xx.xx.xxx.xxx/groupe3
dvc remote modify vm ask_password true
```
La commande `dvc pull` donne ce résultat :
```powershell
(.venv) PS C:\Users\Utilisateur\Desktop\Brief\42_recette_s5\frenchcab\ms_api_metier\ml> dvc pull
WARNING: failed to collect 'workspace', skipping                                                
ERROR: unexpected error - ssh is supported, but requires 'dvc-ssh' to be installed: No module named 'dvc_ssh'

Having any troubles? Hit us up at https://dvc.org/support, we are always happy to help!
```
et sur un autre ordinateur ça donne cette erreur :
```powershell
ERROR: failed to pull data from the cloud - Can't remove the following unsaved files without confirmation. Use --force to force.
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\frenchcab.db
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\yellow_taxi.db
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\models\model_duree_deuxieme.joblib
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\models\model_duree_premier.joblib
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\raw\yellow_tripdata_2026-07.csv
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\raw\taxi_zone_lookup.csv
C:\Users\Utilisateur\Desktop\42. Frenchcab\frenchcab\ms_api_metier\data\raw\yellow_tripdata_2026-07.parquet
(.venv)
```
**Concernant la partie DVC il manque de la documentation sur à quoi il sert, car même avec les écheques le FRONT fonctionne.**

## Le FRONT
Tout fonctionne parfaitement sur https://g3.valentinduflot.fr/nouvelle-reservation
Il marche correctement mais il est demandé de renseigner ou la durée ou la distance et un client ne devrait savoir ça, mis à part s'il va d'abords sur estimation.
** Il n'y a pas de partie sur le FRONT dans `GUIDE_FRENCHCAB.md` ni dans `README.md`. Notamment l'URL : https://g3.valentinduflot.fr/nouvelle-reservation**