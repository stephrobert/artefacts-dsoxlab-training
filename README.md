# Artifact Repositories Training: host, secure and sign what you deploy

**Language:** [English](./README.md) · [Français](./README.fr.md)

[![CI](https://github.com/stephrobert/artefacts-dsoxlab-training/actions/workflows/ci.yml/badge.svg)](https://github.com/stephrobert/artefacts-dsoxlab-training/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://img.shields.io/ossf-scorecard/github.com/stephrobert/artefacts-dsoxlab-training?label=OpenSSF%20Scorecard)](https://securityscorecards.dev/viewer/?uri=github.com/stephrobert/artefacts-dsoxlab-training)
[![Plumber compliance](https://score.getplumber.io/github.com/stephrobert/artefacts-dsoxlab-training.svg)](https://score.getplumber.io/github.com/stephrobert/artefacts-dsoxlab-training)
[![SLSA 3](https://slsa.dev/images/gh-badge-level3.svg)](https://slsa.dev)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](./LICENSE)

Eleven hands-on labs to put an artifact repository into service and make it
trustworthy: install it, proxy a public index, publish your own packages,
serve container images, grant targeted rights, sign what you ship, keep
serving with the Internet cut, and restore after a loss. Every lab runs
against **real Debian 13 machines** and is graded on what the repository
actually serves, never on the commands typed.

Written for sysadmins and DevOps engineers who are asked to host the packages
their deployments depend on, and to answer for them.

## What it is

At the end, a learner can take a bare machine and return a repository that
serves packages and images, that keeps serving when the upstream index is
unreachable, that refuses an unsigned image, that gives each account only the
door it needs, and that comes back after a restore. Each of those is proven by
tests that question the repository through its API, not by reading a
configuration file.

**The order matters, and it is not the order of the topics.** It follows what
a repository needs before the next step is even possible: an instance before a
proxy, a proxy before publishing, publishing before signing. Level 2 then
assumes a repository in service and asks what it takes to trust it.

`dsoxlab next` follows that order, derived from the position of each lab in
`meta.yml`.

### What the tests do, and what they refuse to do

**A lab is graded on the state of the service, never on the commands typed.**

The tests ask the repository itself: its API, the packages it serves, the
images it hands back, the rights it enforces. They do not read the YAML the
learner wrote.

The trap this avoids is a service that answers but serves nothing. A Pulp that
starts and exposes its API proves only that it started, so the labs require a
client machine to really install the package, really pull the image, and
really be refused when the signature is missing.

## Requirements

A missing requirement costs the learner an hour of searching, so this list is
exact and measured against `meta.yml`.

- **Python 3.11+ and [`uv`](https://docs.astral.sh/uv/)**
- **`git`**
- **`dsoxlab`**, the engine, installed as a standalone tool (see below)
- **`terraform`** and **`ansible-playbook`**, which every `vm` lab needs
- **libvirt/KVM 8.0 or above**, the hypervisor the machines run on

Nothing Pulp- or Nexus-related is needed on your own machine: the labs install
them inside the virtual machines, which is the subject of the first lab.

**All eleven labs are `vm` labs**, so `dsoxlab provision` is always needed.

### The machines, and why there are three

Three machines, declared in [`meta.yml`](./meta.yml) on the `lab-artefacts`
network (`10.10.20.0/24`):

| Host | Distribution | vCPU | RAM | Disk | Role |
|---|---|---|---|---|---|
| `depot.lab` | Debian 13 | 2 | 4 GB | 10 GB | the repository under study |
| `client.lab` | Debian 13 | 1 | 1 GB | 10 GB | the consumer, and the proof |
| `nexus.lab` | Debian 13 | 2 | 4 GB | 10 GB | the Nexus option |

About 9 GB of RAM and 30 GB of disk in all. **The client machine is not
scenery**: a repository that answers its own API proves nothing, so the tests
install and pull from a second machine, which is the only way to know that
what is served is usable.

`dsoxlab doctor` says what this repository needs and what it does not, and
tells apart a check that failed from one it could not measure.

## Install

`dsoxlab` is published on [PyPI](https://pypi.org/project/dsoxlab/). Install it
as a standalone tool, so it stays out of this repository:

```bash
# 1. The dsoxlab CLI (external tool, stays out of this repo)
uv tool install dsoxlab

# 2. This lab catalog
git clone https://github.com/stephrobert/artefacts-dsoxlab-training.git
cd artefacts-dsoxlab-training

# 3. Check the contract and the machines
dsoxlab validate-structure
dsoxlab doctor
```

### Your first lab, in five minutes

The machines have to exist first: nothing here runs on your own host.

```bash
export LAB_HOME=$PWD
dsoxlab provision                    # creates depot.lab, client.lab, nexus.lab

dsoxlab list-labs                    # the eleven labs, in teaching order
dsoxlab run       pulp-01-installer  # sets the starting state and opens the session
dsoxlab challenge pulp-01-installer  # read the mission, no step-by-step
dsoxlab check     pulp-01-installer  # run the tests, record the score

dsoxlab clean     pulp-01-installer  # undoes the lab, keeps the machines
dsoxlab destroy                      # gives the machines back
```

`run` is what prepares the lab. Running `check` on a lab you never started
measures nothing, and says so rather than recording a 0.

### Keeping it up to date

```bash
uv tool upgrade dsoxlab        # the engine, published on PyPI
git -C <this repo> pull        # the catalog
```

## How it works

### The declarative contract (two levels)

This repository is **not the CLI**. An engine defect is fixed in
[dsoxlab](https://github.com/stephrobert/dsoxlab), or reported as an issue
there. Here, everything driving the CLI is declarative:

- **`meta.yml`** at the root declares the repository identity, the
  **infrastructure** (provider, network `lab-artefacts`, `10.10.20.0/24` and
  the three hosts) and the **order** of the sections shown by `list-labs`;
- **`lab.yaml`** per lab declares its `skills`, `level`, `runtime`, `distros`,
  `doc_url` and a `validation` block. A `lab.fr.yaml` overrides `title` and
  `description` in French, and nothing else;
- **`setup.yaml`** and **`cleanup.yaml`** lay down and undo the machine state;
- **`challenge/tests/test_functional.py`** carries the proof.

The Terraform and cloud-init templates are **packaged inside dsoxlab**, not
here: this repository declares only its `infra:` block and its public key in
`ssh/`.

### The lab lifecycle

```bash
dsoxlab list-labs              # browse the catalog
dsoxlab show      <id>         # metadata and status of one lab
dsoxlab run       <id>         # lay down the initial state and open the session
dsoxlab challenge <id>         # read the mission, no step-by-step
dsoxlab hint      <id>         # reveal a hint (deducted from the score)
dsoxlab check     <id>         # run the tests, compute and record the score
dsoxlab submit    <id>         # for the exam: a verdict, not a bare score
dsoxlab clean     <id>         # undo the lab, keep the machines
dsoxlab progress               # per-section progress, average score
```

### The validation model, and what is still missing here

Validation **proves the state, it does not trust the learner**, and a lab is
proven **in both directions**: the tests must fail before the work and pass
after it. `scripts/valider-labs.py` requires **0 before and 100 after**.

**This catalog does not yet carry that proof, and saying so is better than
implying it.** It has no `solution/` directory: the eleven labs ship no
reference solution, so the validator has nothing to replay, and
`validation-labs.json` does not exist. Writing those solutions, encrypting
them with `ansible-vault` as the sibling catalogs do, and running the full
cycle is the next piece of work on this repository.

The labs themselves were played by hand on 2026-10-21, test by test. That is
not the same thing as an attestation, and it is not presented as one.

## Catalog

Eleven labs, **6 h 05** in all.

### Level 1: put a repository into service

Four labs and an exam, 3 h 10.

| Lab | What it proves |
|---|---|
| `pulp-01-installer` | Pulp is in service, and its API really answers |
| `pulp-02-proxy` | PyPI is proxied, and the cache serves when the source is cut |
| `pulp-03-publier` | your own package is published, and installed from another machine |
| `pulp-04-registre` | container images are served, and come from your own repository |
| `artefacts-epreuve-n1` | **graded**: the repository nobody documented |

### Level 2: make it a service you can trust

Four labs, 2 h 20.

| Lab | What it proves |
|---|---|
| `pulp-05-securiser` | a targeted role opens one door and not the others |
| `pulp-06-signer` | an image is signed, and verification refuses an unsigned one |
| `pulp-07-air-gap` | the service keeps serving with no Internet, and the cut is real |
| `pulp-08-sauvegarder` | a backup is taken, and the restore really serves again |

### Nexus option

Two labs, 1 h 15. The same two gestures on another engine, for those who run
Nexus rather than Pulp.

| Lab | What it proves |
|---|---|
| `nexus-01-proxy` | a public index is proxied, and the group resolves |
| `nexus-02-registre` | a container registry is hosted, port and realm included |

## Contributing

Read [`CONTRIBUTING.md`](./CONTRIBUTING.md). In short: a lab is proven **in both
directions** before it is merged, `dsoxlab validate-structure` is green, and the
statement exists in English and in French.

A verdict is never committed together with the shared code it measures: the
staleness check compares commit dates, and a verdict written in the same commit
as the files it grades leaves nothing to compare. A hook enforces it.

## License

See [`LICENSE`](./LICENSE).
