# nexus-02-registre

**Public :** l'apprenant.

Ce lab fait héberger un registre d'images de conteneurs par Nexus, avec les
deux réglages que l'installation ne pose pas : le connecteur sur un port
dédié et le realm d'authentification par jetons.

## Ce que vous saurez faire

- Créer un dépôt Docker hébergé et lui attacher un connecteur HTTP sur son
  propre port.
- Reconnaître les symptômes d'un port non publié par le conteneur et d'un
  realm inactif, que les messages d'erreur ne nomment pas.
- Déclarer un registre en clair dans la configuration de podman, et savoir
  pourquoi cela ne se fait qu'en lab.
- Pousser une image puis vérifier, côté Nexus, qu'elle y est bien.

## Ce que ce lab suppose

`nexus-01-proxy`, dont il reprend l'instance : l'EULA y est acceptée, le mot
de passe de `admin` changé et écrit dans `/home/student/.nexus-motdepasse`.
`pulp-04-registre` aide à comparer : chez Pulp, le registre partage le port
et l'authentification de l'API.
