# Formation Dépôts d'artefacts : héberger, sécuriser et signer ce qu'on déploie

**Langue :** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/artefacts-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/artefacts-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/artefacts-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/artefacts-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/artefacts-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/artefacts-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![Licence : CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Onze labs pour mettre un dépôt d'artefacts en service et le rendre digne de
confiance : l'installer, relayer un index public, publier ses propres paquets,
servir des images de conteneurs, accorder des droits ciblés, signer ce qu'on
livre, continuer à servir Internet coupé, et restaurer après une perte. Chaque
lab se joue contre de **vraies machines Debian 13**, et il est noté sur ce que
le dépôt sert réellement, jamais sur les commandes tapées.

Écrit pour les administrateurs et les ingénieurs DevOps à qui l'on demande
d'héberger les paquets dont dépendent leurs déploiements, et d'en répondre.

## Ce que c'est

À la fin, un apprenant sait prendre une machine nue et rendre un dépôt qui
sert paquets et images, qui continue de servir quand l'index amont est
injoignable, qui refuse une image non signée, qui ne donne à chaque compte que
la porte dont il a besoin, et qui revient après une restauration. Chacun de
ces points est prouvé par des tests qui interrogent le dépôt par son API, pas
par la lecture d'un fichier de configuration.

**L'ordre compte, et ce n'est pas celui des sujets.** Il suit ce dont un dépôt
a besoin avant que l'étape suivante soit possible : une instance avant un
relais, un relais avant la publication, la publication avant la signature. Le
niveau 2 suppose ensuite un dépôt en service et demande ce qu'il faut pour lui
faire confiance.

`dsoxlab next` suit cet ordre, dérivé de la position de chaque lab dans
`meta.yml`.

### Ce que les tests font, et ce qu'ils refusent de faire

**Un lab est noté sur l'état du service, jamais sur les commandes tapées.**

Les tests interrogent le dépôt lui-même : son API, les paquets qu'il sert, les
images qu'il rend, les droits qu'il applique. Ils ne lisent pas le YAML écrit
par l'apprenant.

Le piège ainsi évité est celui du service qui répond mais ne sert rien. Un
Pulp qui démarre et expose son API prouve seulement qu'il a démarré : les labs
exigent donc qu'une machine cliente installe vraiment le paquet, tire vraiment
l'image, et se fasse vraiment refuser quand la signature manque.

## Prérequis

Un prérequis manquant coûte une heure de recherche à l'apprenant, donc cette
liste est exacte et mesurée sur `meta.yml`.

- **Python 3.11+ et [`uv`](https://docs.astral.sh/uv/)**
- **`git`**
- **`dsoxlab`**, le moteur, installé en outil autonome (voir plus bas)
- **`terraform`** et **`ansible-playbook`**, dont tout lab `vm` a besoin
- **libvirt/KVM 8.0 ou plus**, l'hyperviseur qui porte les machines

Rien de Pulp ni de Nexus n'est nécessaire sur ton poste : les labs les
installent dans les machines virtuelles, ce qui est le sujet du premier lab.

**Les onze labs sont des labs `vm`**, donc `dsoxlab provision` est toujours
nécessaire.

### Les machines, et pourquoi il y en a trois

Trois machines, déclarées dans [`meta.yml`](./meta.yml) sur le réseau
`lab-artefacts` (`10.10.20.0/24`) :

| Hôte | Distribution | vCPU | RAM | Disque | Rôle |
|---|---|---|---|---|---|
| `depot.lab` | Debian 13 | 2 | 4 Go | 10 Go | le dépôt étudié |
| `client.lab` | Debian 13 | 1 | 1 Go | 10 Go | le consommateur, et la preuve |
| `nexus.lab` | Debian 13 | 2 | 4 Go | 10 Go | l'option Nexus |

Environ 9 Go de RAM et 30 Go de disque en tout. **La machine cliente n'est pas
un décor** : un dépôt qui répond à sa propre API ne prouve rien, donc les
tests installent et tirent depuis une seconde machine, seule façon de savoir
que ce qui est servi est utilisable.

`dsoxlab doctor` dit ce dont ce dépôt a besoin et ce dont il n'a pas besoin, et
distingue un contrôle qui a échoué d'un contrôle qu'il n'a pas pu mesurer.

## Installation

`dsoxlab` est publié sur [PyPI](https://pypi.org/project/dsoxlab/).
Installe-le en outil autonome, pour qu'il reste hors de ce dépôt :

```bash
# 1. La CLI dsoxlab (outil externe, hors de ce dépôt)
uv tool install dsoxlab

# 2. Ce catalogue de labs
git clone https://github.com/stephrobert/artefacts-dsoxlab-training.git
cd artefacts-dsoxlab-training

# 3. Vérifier le contrat et les machines
dsoxlab validate-structure
dsoxlab doctor
```

### Votre premier lab, en cinq minutes

Les machines doivent exister d'abord : rien ici ne tourne sur ton poste.

```bash
export LAB_HOME=$PWD
dsoxlab provision                    # crée depot.lab, client.lab, nexus.lab

dsoxlab list-labs                    # les onze labs, dans l'ordre pédagogique
dsoxlab run       pulp-01-installer  # pose l'état de départ et ouvre la session
dsoxlab challenge pulp-01-installer  # lire la mission, sans pas-à-pas
dsoxlab check     pulp-01-installer  # joue les tests, enregistre le score

dsoxlab clean     pulp-01-installer  # défait le lab, garde les machines
dsoxlab destroy                      # rend les machines
```

C'est `run` qui prépare le lab. Un `check` joué sur un lab jamais démarré ne
mesure rien, et le dit au lieu d'enregistrer un 0.

### Garder à jour

```bash
uv tool upgrade dsoxlab        # le moteur, publié sur PyPI
git -C <ce dépôt> pull         # le catalogue
```

## Comment ça marche

### Le contrat déclaratif, à deux niveaux

Ce dépôt n'est **pas** la CLI. Un défaut du moteur se corrige dans
[dsoxlab](https://github.com/stephrobert/dsoxlab), ou s'y signale par une
issue. Ici, tout ce qui pilote la CLI est déclaratif :

- **`meta.yml`** à la racine déclare l'identité du dépôt, l'**infrastructure**
  (provider, réseau `lab-artefacts`, `10.10.20.0/24` et les trois hôtes) et
  l'**ordre** des sections affichées par `list-labs` ;
- **`lab.yaml`** par lab déclare ses `skills`, son `level`, son `runtime`, ses
  `distros`, son `doc_url` et un bloc `validation`. Un `lab.fr.yaml` surcharge
  `title` et `description` en français, et rien d'autre ;
- **`setup.yaml`** et **`cleanup.yaml`** posent et défont l'état des machines ;
- **`challenge/tests/test_functional.py`** porte la preuve.

Les gabarits Terraform et cloud-init sont **packagés dans dsoxlab**, pas ici :
ce dépôt ne déclare que son bloc `infra:` et sa clé publique dans `ssh/`.

### Le cycle de vie d'un lab

```bash
dsoxlab list-labs              # parcourir le catalogue
dsoxlab show      <id>         # métadonnées et état d'un lab
dsoxlab run       <id>         # poser l'état initial et ouvrir la session
dsoxlab challenge <id>         # lire la mission, sans pas-à-pas
dsoxlab hint      <id>         # révéler un indice (déduit du score)
dsoxlab check     <id>         # jouer les tests, calculer et enregistrer le score
dsoxlab submit    <id>         # pour l'épreuve : un verdict, pas un score
dsoxlab clean     <id>         # défaire le lab, garder les machines
dsoxlab progress               # progression par section, score moyen
```

### Le modèle de validation, et ce qui manque encore ici

La validation **prouve l'état, elle ne fait pas confiance**, et un lab est
prouvé **dans les deux sens** : les tests doivent échouer avant le travail et
passer après. `scripts/valider-labs.py` exige **0 avant et 100 après**.

**Ce catalogue ne porte pas encore cette preuve, et le dire vaut mieux que de
le laisser supposer.** Il n'a aucun répertoire `solution/` : les onze labs ne
livrent aucun corrigé de référence, le validateur n'a donc rien à rejouer, et
`validation-labs.json` n'existe pas. Écrire ces corrigés, les chiffrer par
`ansible-vault` comme le font les catalogues frères, et jouer le cycle complet
est le prochain travail sur ce dépôt.

Les labs eux-mêmes ont été joués à la main le 2026-10-21, test par test. Ce
n'est pas la même chose qu'une attestation, et ce n'est pas présenté comme
telle.

## Catalogue

Onze labs, **6 h 05** en tout.

### Niveau 1 : mettre un dépôt en service

Quatre labs et une épreuve, 3 h 10.

| Lab | Ce qu'il prouve |
|---|---|
| `pulp-01-installer` | Pulp est en service, et son API répond vraiment |
| `pulp-02-proxy` | PyPI est relayé, et le cache sert quand la source est coupée |
| `pulp-03-publier` | votre propre paquet est publié, et installé depuis une autre machine |
| `pulp-04-registre` | les images de conteneurs sont servies, et viennent de votre dépôt |
| `artefacts-epreuve-n1` | **évalué** : le dépôt que personne n'a documenté |

### Niveau 2 : en faire un service de confiance

Quatre labs, 2 h 20.

| Lab | Ce qu'il prouve |
|---|---|
| `pulp-05-securiser` | un rôle ciblé ouvre une porte et pas les autres |
| `pulp-06-signer` | une image est signée, et la vérification refuse celle qui ne l'est pas |
| `pulp-07-air-gap` | le service sert toujours sans Internet, et la coupure est réelle |
| `pulp-08-sauvegarder` | une sauvegarde est prise, et la restauration sert de nouveau |

### Option Nexus

Deux labs, 1 h 15. Les deux mêmes gestes sur un autre moteur, pour qui exploite
Nexus plutôt que Pulp.

| Lab | Ce qu'il prouve |
|---|---|
| `nexus-01-proxy` | un index public est relayé, et le groupe résout |
| `nexus-02-registre` | un registre d'images est hébergé, port et realm compris |

## Contribuer

Lire [`CONTRIBUTING.md`](./CONTRIBUTING.md). En résumé : un lab est prouvé
**dans les deux sens** avant d'être fusionné, `dsoxlab validate-structure` est
vert, et l'énoncé existe en anglais et en français.

Un verdict ne se commite jamais avec le code partagé qu'il mesure : le contrôle
de péremption compare des dates de commit, et un verdict écrit dans le même
commit que les fichiers qu'il note ne laisse rien à comparer. Un hook l'impose.

## Licence

Voir [`LICENSE`](./LICENSE).
