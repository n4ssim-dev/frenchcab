# MLOps : DVC + MLflow

Ce document explique comment reproduire les donnees, le pipeline d'entrainement et le suivi des experiences de `ms_api_metier`.

| Outil | Role |
|---|---|
| Git | Code, `dvc.yaml`, `dvc.lock`, `params.yaml`, fichiers `*.dvc` |
| DVC | Donnees volumineuses (bases `.db`, CSV, modeles `.joblib`) et pipeline reproductible |
| MLflow | Suivi des entrainements (parametres, metriques, graphiques) et registre de modeles |

## 1. Installation

```bash
cd ms_api_metier
pip install -r requirements.txt
pip install -r requirements-ml.txt      # dvc + mlflow (inutiles pour l'API / Docker)
```

## 2. Recuperer les donnees

Configurer le remote DVC partage (une seule fois, les identifiants restent en local) :

```bash
dvc remote add -d -f storage ssh://groupe3@xx.xx.xxx.xxx/groupe3
dvc remote modify vm ask_password true
dvc pull
```

Ne jamais commiter `.dvc/config.local` (mots de passe, cles).

## 3. Le pipeline (`dvc.yaml`)

```
data/raw --> etl --> load
              \--> train --> evaluate
```

| Etape | Commande | Produit |
|---|---|---|
| `etl` | `python etl.py` | CSV propre, `yellow_taxi.db` |
| `load` | `python load.py` | `frenchcab.db` |
| `train` | `python ml/stage_train.py` | modeles `.joblib`, graphique de comparaison |
| `evaluate` | `python ml/stage_evaluate.py` | metriques d'evaluation (seuil de MAE dans `params.yaml`) |

```bash
dvc repro        # ne relance que les etapes dont les entrees ont change
dvc dag          # affiche le graphe
dvc status       # indique ce qui est a jour ou non
```

Les parametres modifiables sont dans `params.yaml` (date de debut et seuil de MAE de l'evaluation).

## 4. Suivre les experiences avec MLflow

Chaque `dvc repro` des etapes `train` et `evaluate` cree un run dans l'experience `frenchcab-duree-trajet` (parametres, metriques, graphique, tags `git_commit` et `dvc_md5_yellow_taxi_db` pour retrouver le code et les donnees exacts).

```bash
cd ms_api_metier
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Ouvrir http://127.0.0.1:5000, passer en vue **Model training** (et non GenAI), choisir l'experience `frenchcab-duree-trajet`, onglet **Runs**.

## 5. Registre de modeles (a la demande)

```bash
python ml/register_model.py                    # alias "champion"
python ml/register_model.py --modele deuxieme  # alias "challenger"
```

Chargement dans du code : `mlflow.sklearn.load_model(
    "models:/frenchcab-duree-trajet@champion",
    skops_trusted_types=["sklearn.tree._tree.Tree"],
)`.
Le modele est copie dans `mlruns/` (plusieurs Go) : ne l'enregistrer que lorsqu'on veut le promouvoir.

## 6. Modifier les donnees ou le code

1. Modifier le code, `params.yaml` ou les donnees brutes.
2. `dvc repro`
3. `git add dvc.lock params.yaml <fichiers modifies>` (fichiers un par un, jamais `git add .`)
4. `git commit`
5. `dvc push` **puis** `git push` (sinon les collegues ne retrouvent pas les donnees).

Nouveau fichier de donnees brut : `dvc add data/<fichier>` puis `git add data/<fichier>.dvc data/.gitignore`.

## 7. Retrouver un ancien resultat

```bash
git checkout <commit_du_run_mlflow>
dvc checkout        # remet les donnees correspondantes
```

## 8. Depannage

| Probleme | Solution |
|---|---|
| Je ne vois pas les runs dans MLflow | Vue Model training, bonne experience, interface lancee depuis `ms_api_metier` |
| `dvc pull` echoue | Verifier `dvc remote list` et `.dvc/config.local` |
| `dvc add` refuse un fichier | Il est ignore par `.gitignore` : retirer la regle correspondante |
| `ERROR: ... already exists` sur un remote | Utiliser `-f` : `dvc remote add -d -f ...` |
