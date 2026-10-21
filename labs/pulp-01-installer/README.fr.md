# pulp-01-installer

**Public :** l'apprenant.

Mettre un dépôt d'artefacts Pulp en service sur une machine neuve, et prouver
qu'il répond vraiment, pas seulement qu'un conteneur tourne.

## Ce que vous saurez faire

- Démarrer Pulp en conteneur avec une image **épinglée sur sa version**.
- Déclarer l'**URL publique** par laquelle les clients joindront l'instance,
  et comprendre pourquoi `localhost` y est un piège.
- Poser le mot de passe du compte `admin` et vérifier qu'il est réellement
  exigé.
- Configurer la CLI `pulp` pour qu'elle dialogue avec l'instance sans
  identifiants sur la ligne de commande.
- Faire revenir le service après un redémarrage, ce qui, en **rootless**,
  demande plus que `--restart=always`.

## Durée

Environ 35 minutes, dont une minute d'attente pendant les migrations de la
première mise en service.

## Ce qui est fourni

La machine `depot.lab` porte déjà **podman** et l'**image Pulp**. Rien
d'autre : ni conteneur, ni configuration, ni compte.

## Comment on est noté

Sept tests, qui interrogent l'instance comme le ferait un client : le
conteneur tourne et son image est épinglée, le service revient après un
reboot, l'API répond et annonce ses composants, l'URL publique est joignable
depuis le réseau, le mot de passe admin est exigé (et un mauvais mot de passe
refusé), et la CLI répond depuis le compte `student`.
