# pulp-05-securiser

**Public :** l'apprenant.

Donner à un compte le droit de faire une chose, et prouver qu'il ne peut pas
en faire d'autres.

## Ce que vous saurez faire

- Créer un **compte limité** sur Pulp.
- Lui accorder un **rôle ciblé**, globalement.
- Vérifier qu'un droit accordé **ouvre une porte** et une seule.

## Durée

Environ 30 minutes.

## Ce que ce lab a appris en étant écrit

Sa première version demandait un compte « en lecture seule ». Mesuré sur
l'instance : **un compte Pulp neuf, sans aucun rôle, lit déjà le catalogue et
se voit refuser l'écriture.** Le test était donc vert sans que personne ait
accordé quoi que ce soit.

Dans Pulp, on n'enlève pas des droits : on en ajoute. La preuve d'un rôle
bien posé est une porte ouverte **et** les autres restées fermées.

## Un détail qui bloque dix minutes

Un rôle global s'accorde avec **`--object ""`**. Sans cette option, la CLI
répond `--object must be set when not using --domain`, et l'attribution
échoue en silence si on ne lit pas sa sortie.
