# Contexte
Ce fichier vise à définir les rêgle de contribution collaboratives dans le cadre du projet "FrenchCab".

# Règles

## Branches

Les branches devront toutes suivre cette appelation et être écrites en minuscule sans ponctuation ni accent ni caractères spéciaux : 

```:nom:```  (exemple:  ```malick```)

## Commits
Les commits devront être précédés de ces balises écrites en miniscule et sans ponctuation :

```<feat>``` ```<fix>``` ```<docs>``` ```<chores>```

## Dépôt distant
- Avant chaque push sur le dépot distant, il devra être effectué un pull de la branche de développement principale (```dev```).
- Chaque push devra être réalisé sur sa propre branche distante.
- L'intégrateur devra être informé de ce push afin qu'il puisse gérer les merges sur les 2 branches principales (```dev``` et ```main```)
- Lorsque le projet atteint un niveau satisfaisant sans bugs ni conflit, un merge sur la branche ```main```est envisageable.
- L'intégrateur a la charge de s'assurer de la santé de la branche de développement principale (```dev```) ainsi que la branche ```main```.

## Convention d'écriture
Chaque fonction doit être commenter de manière claire et précise.
Le camel case est utiliser comme convention d'écriture. 

## Tests
Des tests automatisés doivent être définis pour couvrir 100% du code.