# Servir des images de conteneurs, et prouver qu'elles viennent de chez vous

Les builds de l'équipe tirent leurs images de base depuis Docker Hub. Deux
fois ce mois-ci, la limite de téléchargements a fait échouer la chaîne en
pleine journée. On vous demande de servir ces images depuis votre dépôt.

## Ce que vous devez obtenir

1. L'**authentification par jeton** activée sur Pulp. Sans elle, l'API de
   registre ne fonctionne pas : `/v2/` doit répondre **401**, pas 500.

2. Un **remote pull-through** vers Docker Hub, nommé `dockerhub`.

3. Une **distribution pull-through** qui l'expose sous le chemin
   `dockerhub`.

4. Depuis `client.lab`, un `podman pull` qui **réussit en passant par votre
   dépôt** pour une image publique.

5. L'image tirée doit **porter l'adresse de votre dépôt** : c'est la preuve
   qu'elle n'est pas venue directement de Docker Hub.

## Le piège, et il est réel

Fournir son propre `settings.py` empêche l'image Pulp de générer les réglages
de jeton par défaut. `/v2/` répond alors **500** avec `AttributeError:
TOKEN_SERVER` dans les journaux. Un 500 ressemble à une panne : c'est une
configuration incomplète. Il faut déclarer `TOKEN_SERVER`,
`TOKEN_SIGNATURE_ALGORITHM`, `PUBLIC_KEY_PATH` et `PRIVATE_KEY_PATH`, puis
**générer la paire de clés** et redémarrer le conteneur.

## Ce qui est vérifié

- `/v2/` répond **401** : le jeton est actif et correctement configuré ;
- le remote pull-through existe et vise bien le registre Docker ;
- la distribution existe sous le chemin attendu ;
- depuis `client.lab`, `podman pull` réussit à travers le dépôt ;
- l'image présente localement porte **l'adresse du dépôt**, pas `docker.io`.

## Indices

- Les réglages de jeton se posent dans le même `settings.py` que
  `CONTENT_ORIGIN`, et le conteneur doit **redémarrer** pour les lire.
- La paire de clés se génère avec `openssl ecparam -genkey -name prime256v1`.
- Le remote et la distribution pull-through se créent par l'**API REST** : la
  CLI ne les expose pas encore.
- En HTTP, `podman` a besoin de `--tls-verify=false`.
