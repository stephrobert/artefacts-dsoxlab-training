# Accorder un rôle ciblé, et prouver qu'il n'ouvre qu'une porte

Tout le monde se connecte au dépôt avec le compte `admin`, dont le mot de
passe circule dans un fichier partagé. L'équipe qui livre les bibliothèques
internes n'a pourtant besoin que d'une chose : **créer des dépôts de
fichiers**. Pas de toucher aux images, pas d'administrer l'instance.

## Ce que vous devez obtenir

1. Un compte **`publieur`** sur Pulp, avec son propre mot de passe. Déposez
   ce mot de passe dans **`/home/student/.publieur-motdepasse`**, sur une
   seule ligne : la validation en a besoin pour s'authentifier comme ce
   compte et vérifier ce qu'il peut faire.

2. Ce compte doit pouvoir **créer un dépôt de fichiers**.

3. Ce compte ne doit **pas** pouvoir créer un **dépôt de conteneurs**.

4. Le compte `admin` doit, lui, toujours pouvoir tout faire.

## Pourquoi ce lab a été réécrit, et ce que ça vous apprend

Sa première version demandait simplement un compte « en lecture seule ».
Mesuré sur l'instance : **un compte Pulp neuf, sans aucun rôle, lit déjà le
catalogue et se voit refuser l'écriture.** La lecture seule est donc l'état
par défaut, et un test qui s'en contentait était vert sans que personne ait
accordé quoi que ce soit.

C'est un enseignement en soi : **dans Pulp, on n'enlève pas des droits, on en
ajoute**. Un rôle ouvre une porte précise. La preuve d'un rôle bien posé,
c'est donc une porte ouverte **et** les autres restées fermées.

## Ce qui est vérifié

- le compte `publieur` existe et s'**authentifie** (un mauvais mot de passe
  est refusé) ;
- il **crée** un dépôt de fichiers : HTTP 201 ;
- il **ne crée pas** de dépôt de conteneurs : HTTP 403 ;
- le compte `admin` crée encore les deux.

## Indices

- `pulp role list` montre les 175 rôles de l'instance. Ceux qui autorisent la
  création se terminent par `_creator`.
- Un rôle **global** s'accorde avec `--object ""` : sans cette option, la CLI
  répond `--object must be set when not using --domain`.
- Pour tester une permission, un `curl -u` avec les identifiants du compte
  limité suffit.
