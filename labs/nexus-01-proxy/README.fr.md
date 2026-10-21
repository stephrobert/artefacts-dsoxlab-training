# nexus-01-proxy

**Public :** l'apprenant.

Ce lab met un Nexus Repository en service devant PyPI, et referme les deux
portes que l'installation laisse ouvertes.

## Ce que vous saurez faire

- Changer le mot de passe jetable que Nexus génère au premier démarrage, et
  savoir où il est écrit.
- Créer un dépôt proxy par l'API REST de Nexus, et comprendre pourquoi un
  proxy y est un type de dépôt plutôt qu'un assemblage.
- Vérifier qu'un cache s'est réellement rempli, et pas seulement qu'il est
  configuré.
- Couper l'accès anonyme, que Nexus laisse actif par défaut.
- Installer un paquet à travers le dépôt en s'authentifiant.

## Ce que ce lab suppose

Le lab `pulp-02-proxy` : le même geste avec Pulp, auquel celui-ci se compare
en permanence. Ce lab tourne sur `nexus.lab`, machine distincte de celle de
Pulp.
