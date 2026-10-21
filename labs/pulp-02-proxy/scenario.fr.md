# Proxyfier PyPI, et prouver que le cache sert quand la source tombe

Votre instance Pulp tourne sur `depot.lab`. Elle ne sert encore rien : c'est
une coquille vide. On vous demande d'en faire le **proxy PyPI** de l'équipe,
pour que les builds cessent de dépendre de la disponibilité de PyPI.

La machine `client.lab` jouera le rôle du poste de développement, ou du
runner de CI : c'est depuis elle que l'installation doit réussir.

## Ce que vous devez obtenir

1. Un **remote** qui pointe vers PyPI et ne rapatrie qu'un paquet nommé,
   `six`. Synchroniser PyPI en entier prendrait des heures et des dizaines
   de gigaoctets.

2. Un **dépôt** synchronisé depuis ce remote, et **publié**.

3. Une **distribution** qui expose l'index à une adresse stable, sous le nom
   `pypi`.

4. Depuis `client.lab`, un `pip install` qui **réussit en passant par le
   dépôt**, dans un environnement virtuel, sans jamais joindre PyPI.

5. Le paquet **servi depuis le cache** : une fois l'accès à PyPI coupé sur
   `depot.lab`, la même installation doit **encore réussir**.

## Le piège des dépendances

`six` est choisi parce qu'il n'a **aucune dépendance**. Ce n'est pas un
détail : un remote qui ne rapatrie qu'un paquet ne sert pas celles des
autres. Essayez avec un paquet qui en a, et `pip` listera parfaitement toutes
ses versions depuis votre index, puis échouera sur
`ResolutionImpossible` : le dépôt sert, mais pas de quoi résoudre.

En production, la liste `includes` d'un remote doit donc couvrir **l'arbre de
dépendances complet**, ou n'être pas limitée du tout.

## Pourquoi le dernier point est le seul qui prouve quelque chose

Un proxy qui n'a rien mis en cache fonctionne parfaitement tant qu'Internet
répond : il relaie. Il est alors **indiscernable** d'un vrai cache, et vous
découvrirez la différence le jour où PyPI tombera, c'est-à-dire au pire
moment. La seule preuve d'un cache est de lui **retirer sa source** et de
constater qu'il sert quand même.

C'est ce que fait la validation : elle coupe l'accès sortant vers PyPI sur
`depot.lab`, relance l'installation depuis `client.lab`, et la rétablit
ensuite.

## Ce qui est vérifié

- le remote existe, vise PyPI, et ne syncronise qu'un paquet nommé ;
- le dépôt a bien une version synchronisée qui contient du contenu ;
- la distribution répond, et son index est lisible ;
- `pip install` réussit depuis `client.lab` en passant par le dépôt ;
- **la même installation réussit encore une fois PyPI injoignable** ;
- rien ne dépend d'un paquet déjà présent sur le client : l'environnement
  virtuel est neuf.

## Indices

- `pulp python remote create --help` montre l'option qui limite la
  synchronisation à une liste de paquets.
- Une synchronisation est une **tâche** : `pulp task list` dit où elle en est.
- L'adresse de l'index servi par la distribution se termine par `/simple/`.
- Côté client, `pip install --index-url` suffit : rien à configurer
  globalement.
