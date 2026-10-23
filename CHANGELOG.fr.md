# Journal des modifications

Les changements notables de ce catalogue sont consignés ici. Le format suit
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce catalogue suit
le [versionnage sémantique](https://semver.org/lang/fr/).

**Ce qu'une version veut dire ici.** Un catalogue n'est pas une bibliothèque :
un incrément MINEUR ajoute des labs, un CORRECTIF corrige un énoncé ou un test
sans changer ce qu'un lab prouve, et un incrément MAJEUR renomme ou retire des
labs, ce qui casse la progression déjà enregistrée des apprenants.

## [Non publié]

### Ajouté

- **Les corrigés de référence de huit des onze labs**, chiffrés sous
  `solution/` : de `pulp-01` à `pulp-08`. Chacun est écrit depuis les tests,
  qui sont la spécification, et depuis le `setup.yaml`, qui est l'état de
  départ ; chacun porte en en-tête ce que son lab prouve et le piège autour
  duquel il est bâti, parce qu'un corrigé qui se contente de marcher n'est un
  corrigé qu'à moitié.

  **Ils ne sont pas encore attestés.** `scripts/verify-solutions.py` ne les a
  jamais joués : cela demande les trois machines et une campagne dédiée. D'ici
  là, ce sont des brouillons relus, pas des réponses prouvées.

- Restent à écrire : `nexus-01-proxy`, `nexus-02-registre` et
  `artefacts-epreuve-n1`.

### Défauts relevés en écrivant les corrigés

- `pulp-05-securiser` nettoie dans son `setup.yaml` un compte nommé
  `lecteur`, vestige de la version précédente du lab, alors que le compte
  qu'il demande désormais s'appelle `publieur`. Le lab ne se remet donc pas à
  zéro entre deux tentatives, et un apprenant qui a accordé un rôle trop
  large le conserve.

- Le troisième test de `pulp-02-proxy` lit `distributions[0]` sans filtrer
  sur le nom, là où `pulp-03`, `pulp-07` et `pulp-08` filtrent tous. Si un
  autre lab laisse une distribution derrière lui, ce test vise la mauvaise.

## [0.1.0] - 2026-10-23

### Ajouté

- **Première publication.** Onze labs pour mettre un dépôt d'artefacts en
  service et le rendre digne de confiance, 6 h 05 en tout, sur trois machines
  Debian 13 : le dépôt étudié, un client qui prouve que ce qui est servi est
  utilisable, et l'option Nexus.

- **La chaîne de contribution des catalogues frères** : Zizmor, Actionlint,
  Poutine, parité pre-commit et CodeQL sur `python` et `actions`, plus
  Plumber, Scorecard, Dependabot et les gabarits d'issue. La CI passe d'un job
  à **six**, pour sept contrôles requis, et `main` porte le même ruleset que
  les autres : historique linéaire, pull request avec une revue, et les sept
  contrôles.

- Le hook qui refuse un verdict commité avec ce qu'il mesure, et le jeu de
  règles `ruff` commun à la collection.

### Manques connus

- **Aucun corrigé de référence, donc aucune attestation.** Ce catalogue n'a pas
  de répertoire `solution/` : `scripts/valider-labs.py` n'a rien à rejouer,
  `validation-labs.json` n'existe pas, et aucun lab ne porte de verdict. Les
  labs ont été joués à la main le 2026-10-21, ce qui n'est pas la même chose
  et n'est pas présenté comme telle. Écrire les onze corrigés, les chiffrer par
  `ansible-vault` et jouer le cycle complet est le prochain travail ici.
