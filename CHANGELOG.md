# Changelog

All notable changes to this catalog are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this catalog
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**What a version means here.** A catalog is not a library: a MINOR bump adds
labs, a PATCH fixes a statement or a test without changing what a lab proves,
and a MAJOR renames or removes labs, which breaks the progress already recorded
by learners.

## [Unreleased]

### Added

- **Reference solutions for eight of the eleven labs**, encrypted under
  `solution/`: `pulp-01` through `pulp-08`. Each one is written from the
  tests, which are the specification, and from the `setup.yaml`, which is the
  starting state; each carries in its header what its lab proves and the trap
  it is built around, because a solution that only works is half a solution.

  **They have not been attested yet.** `scripts/verify-solutions.py` has never
  played them: that needs the three machines and a dedicated campaign. Until
  it has, treat them as reviewed drafts, not as proven answers.

- Still missing: `nexus-01-proxy`, `nexus-02-registre` and
  `artefacts-epreuve-n1`.

### Known defects, found while writing the solutions

- `pulp-05-securiser` cleans up an account named `lecteur` in its
  `setup.yaml`, a leftover from the earlier version of the lab, while the
  account it now asks for is `publieur`. The lab therefore does not reset
  between two attempts, and a learner who granted too broad a role keeps it.

- The third test of `pulp-02-proxy` reads `distributions[0]` without
  filtering on the name, where `pulp-03`, `pulp-07` and `pulp-08` all filter.
  Should another lab leave a distribution behind, that test aims at the wrong
  one.

## [0.1.0] - 2026-10-23

### Added

- **First publication.** Eleven labs to put an artifact repository into
  service and make it trustworthy, 6 h 05 in all, on three Debian 13 machines:
  the repository under study, a client that proves what is served is usable,
  and the Nexus option.

- **The contribution chain of the sibling catalogs**: Zizmor, Actionlint,
  Poutine, pre-commit parity and CodeQL on `python` and `actions`, plus
  Plumber, Scorecard, Dependabot and the issue templates. The CI goes from one
  job to **six**, for seven required checks, and `main` carries the same
  ruleset as the others: linear history, pull request with one review, and the
  seven checks.

- The hook that refuses a verdict committed together with what it measures,
  and the `ruff` rule set shared by the collection.

### Known gaps

- **No reference solution, and therefore no attestation.** This catalog has no
  `solution/` directory: `scripts/valider-labs.py` has nothing to replay, so
  `validation-labs.json` does not exist and no lab carries a verdict. The labs
  were played by hand on 2026-10-21, which is not the same thing and is not
  presented as one. Writing the eleven solutions, encrypting them with
  `ansible-vault` and running the full cycle is the next work here.
