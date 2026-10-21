# Mettre Pulp en service, et prouver que l'API répond

Votre équipe tire ses dépendances directement des dépôts publics. Au dernier
incident, PyPI a été injoignable vingt minutes et plus aucun build ne passait.
On vous demande de monter un **dépôt d'artefacts** interne, qui servira de
proxy aux dépôts publics et hébergera plus tard vos propres paquets.

La machine `depot.lab` vous attend avec **podman** installé et l'image de Pulp
déjà tirée. Rien d'autre : pas de conteneur, pas de configuration, pas de
compte.

## Ce que vous devez obtenir

1. **Pulp tourne** dans un conteneur nommé `pulp`, et il **repart tout seul**
   après un redémarrage de la machine. Un dépôt qui ne remonte pas arrête la
   chaîne de build au premier reboot.

2. **L'API répond** sur le port **8080** : `http://depot.lab:8080/pulp/api/v3/status/`
   renvoie un JSON qui liste ses composants.

3. **L'URL publique annoncée est la bonne.** Pulp construit les liens de
   téléchargement qu'il sert à ses clients à partir du paramètre
   `CONTENT_ORIGIN`. S'il annonce une adresse par laquelle personne ne peut
   l'atteindre, l'instance paraît saine et tous les `pip install` échoueront
   sur des liens cassés. Les clients joindront ce dépôt **depuis une autre
   machine** : `localhost` n'est donc pas la bonne réponse.

4. **Le compte `admin` a un mot de passe** et l'authentification fonctionne
   sur l'API.

5. **La CLI `pulp` est installée et configurée** pour cette instance : lancée
   sans argument de connexion, elle doit dialoguer avec elle.

## Ce qui est vérifié

La validation ne regarde pas votre historique de commandes ni le nom de vos
répertoires. Elle interroge l'instance comme le ferait un client :

- un conteneur `pulp` est en cours d'exécution, et sa politique de
  redémarrage le fait revenir après un reboot ;
- l'API de statut répond, et annonce bien ses composants ;
- l'URL publique que Pulp annonce correspond à celle par laquelle on
  l'atteint réellement depuis le réseau ;
- une requête authentifiée en `admin` est acceptée, une requête avec un
  mauvais mot de passe est refusée ;
- la CLI répond depuis le compte `student`, sans qu'on lui passe l'adresse ni
  les identifiants sur la ligne de commande ;
- l'image utilisée est **épinglée** sur une version, jamais `latest`.

## Indices

- Le paramètre `CONTENT_ORIGIN` se pose dans un fichier `settings.py` monté
  dans le conteneur sur `/etc/pulp`.
- Le mot de passe admin se pose **une fois l'instance démarrée**, avec
  `pulpcore-manager reset-admin-password`.
- La CLI lit sa configuration dans `~/.config/pulp/cli.toml`.
- L'initialisation prend environ une minute : tant que l'API refuse la
  connexion, le conteneur finit de démarrer.
