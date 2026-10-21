# pulp-02-proxy

**Public :** l'apprenant.

Faire d'une instance Pulp vide le proxy PyPI de l'équipe, et prouver qu'elle
sert encore quand PyPI tombe.

## Ce que vous saurez faire

- Créer un **remote** vers un dépôt public et **limiter** ce qu'il rapatrie.
- Synchroniser un **dépôt**, et vérifier que sa version contient vraiment du
  contenu.
- Exposer l'index par une **distribution**, à une adresse stable.
- Installer un paquet depuis **une autre machine** en passant par ce dépôt.
- Distinguer un **cache** d'un simple **relais**, en coupant la source.

## Durée

Environ 40 minutes.

## Ce qui est fourni

Une instance Pulp déjà en service sur `depot.lab` (c'est le lab précédent),
et un poste `client.lab` prêt à installer.

## Deux pièges que ce lab enseigne

- **Les dépendances.** Un remote limité à un paquet ne sert pas celles des
  autres : `pip` listera toutes les versions depuis votre index, puis
  échouera sur `ResolutionImpossible`.
- **L'URL publique.** `base_url` d'une distribution est construit à partir de
  l'hôte de la requête API : interrogée depuis le conteneur, elle annonce une
  adresse que personne ne peut joindre. L'adresse à donner aux clients se
  construit depuis celle du dépôt et le `base_path`.
