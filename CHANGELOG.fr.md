# Journal des modifications

Les changements notables de ce catalogue sont consignés ici. Le format suit
[Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et ce catalogue suit
le [versionnage sémantique](https://semver.org/lang/fr/).

**Ce qu'une version veut dire ici.** Un catalogue n'est pas une bibliothèque :
un incrément MINEUR ajoute des labs, un CORRECTIF corrige un énoncé ou un test
sans changer ce qu'un lab prouve, et un incrément MAJEUR renomme ou retire des
labs, ce qui casse la progression déjà enregistrée des apprenants.

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
