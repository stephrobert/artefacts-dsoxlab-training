# pulp-02-proxy

**Audience:** the learner.

Turn an empty Pulp instance into the team's PyPI proxy, and prove it still
serves when PyPI goes down.

## What you will be able to do

- Create a **remote** to a public repository and **limit** what it fetches.
- Sync a **repository**, and check its version actually holds content.
- Expose the index through a **distribution**, at a stable address.
- Install a package from **another machine** through that repository.
- Tell a **cache** from a plain **relay**, by cutting the source.

## Duration

About 40 minutes.

## What you are given

A Pulp instance already in service on `depot.lab` (that is the previous lab),
and a `client.lab` workstation ready to install.

## Two traps this lab teaches

- **Dependencies.** A remote limited to one package does not serve anyone
  else's: `pip` will list every version from your index, then fail with
  `ResolutionImpossible`.
- **The public URL.** A distribution's `base_url` is built from the host of
  the API request: queried from inside the container, it advertises an
  address nobody can reach. The address to hand to clients is built from the
  repository's own address and the `base_path`.
