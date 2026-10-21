# pulp-08-sauvegarder

**Public :** l'apprenant.

Ce lab apprend à sauvegarder le contenu d'un dépôt Pulp et, surtout, à
prouver que la restauration sert réellement un client.

## Ce que vous saurez faire

- Autoriser un chemin d'export et un chemin d'import dans la configuration
  de Pulp, et savoir que ces réglages ne sont relus qu'au démarrage.
- Produire un export d'un dépôt, et reconnaître ses deux fichiers
  indissociables : l'archive et sa table des matières.
- Sortir une sauvegarde de la machine qu'elle protège.
- Lancer un import par l'API, parce que le CLI ne sait pas le faire.
- Publier le dépôt restauré et vérifier qu'un client s'installe depuis lui.

## Ce que ce lab suppose

`pulp-01-installer` pour l'instance, et `pulp-03-publier` pour le dépôt
`interne` qui sert de matière à sauvegarder.
