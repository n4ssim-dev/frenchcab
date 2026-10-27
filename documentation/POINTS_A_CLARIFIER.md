# Points à clarifier

En fusionnant les README d'origine, des incohérences ou des trous ont été relevés. À vérifier auprès de l'équipe précédente ou dans le code :

1. **PostgreSQL** : mentionné dans les notes de départ comme « base analytique », mais le projet utilise DuckDB et SQLite (voir [README_DONNEES](README_DONNEES.md#les-deux-bases-du-projet)).
2. **Seuils de nettoyage différents** : `etl.py` retire les courses de plus de 320 miles ou 7 h ; l'entraînement ne garde que 0,1 à 80 miles et 1 à 180 min. Ce n'est pas forcément un bug (deux filtres successifs), mais c'est à savoir.
3. **Fréquence du pipeline MLOps** sur la VM : toutes les 15 minutes, ce qui est très fréquent pour un entraînement lourd.
4. **Chemins différents sur la VM** : `/home/groupe3/frenchcab` pour le déploiement, `/home/ubuntu/frenchcab` pour le script MLOps. Vérifier lequel est le bon.
5. **Nom du script** `mlops.hs` : probablement une faute de frappe pour `mlops.sh`.
6. **Horaires de déploiement** : l'ancien README principal parlait de 11h et 15h, la doc MLOps de 11h, 15h et 15h20.
7. **Tests Python désactivés dans la CI** (voir [DEPLOIEMENT](DEPLOIEMENT.md#cicd--automatiser)).
8. **`model_info.py`** lit un fichier (`model_duree_extra_trees.joblib`) que l'entraînement ne produit pas.
9. **Adresse IP et accès du stockage DVC** : masqués (`xx.xx.xxx.xxx`), à demander à l'équipe.
