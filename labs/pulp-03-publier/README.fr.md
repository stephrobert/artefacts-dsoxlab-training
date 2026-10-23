# pulp-03-publier

**Public :** l'apprenant.

Héberger dans Pulp un paquet que l'équipe produit, et l'installer depuis une
autre machine.

## Ce que vous saurez faire

- Construire une **distribution Python** à partir d'un `pyproject.toml`.
- **Téléverser** un paquet dans Pulp et l'ajouter à un dépôt.
- L'**exposer** par une distribution.
- L'**installer depuis un autre hôte**, dans un environnement neuf.

## Durée

Environ 35 minutes.

## Ce qui est fourni

L'instance Pulp du premier lab, les outils de construction côté dépôt, et de
quoi installer côté client.

## Pourquoi le nom du paquet est inventé

`outils-maison-lab` n'existe sur aucun dépôt public. Si le lab faisait
publier un paquet connu, l'installation pourrait réussir sans que votre dépôt
serve à rien : pip irait le chercher ailleurs. Ici, un succès prouve que le
paquet vient de chez vous.

## Un détail qui coûte dix minutes

`pulp python content create` (qui remplace `content upload`, dépréciée depuis
pulp-cli 0.38.0) exige **`--relative-path`**, le nom sous lequel
le fichier sera servi. Sans lui, la commande refuse, et le message ne le dit
qu'en affichant son usage.
