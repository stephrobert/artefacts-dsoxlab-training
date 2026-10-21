# Proxy PyPI, and prove the cache serves when the source goes down

Your Pulp instance is running on `depot.lab`. It serves nothing yet: it is an
empty shell. You are asked to turn it into the team's **PyPI proxy**, so that
builds stop depending on PyPI being up.

The `client.lab` machine plays the developer workstation, or the CI runner: it
is from there that the installation must succeed.

## What you must achieve

1. A **remote** pointing at PyPI that only fetches one named package,
   `six`. Syncing the whole of PyPI would take hours and tens of gigabytes.

2. A **repository** synced from that remote, and **published**.

3. A **distribution** exposing the index at a stable address, under the name
   `pypi`.

4. From `client.lab`, a `pip install` that **succeeds through the repository**,
   in a virtual environment, without ever reaching PyPI.

5. The package **served from the cache**: once access to PyPI is cut on
   `depot.lab`, the same installation must **still succeed**.

## The dependency trap

`six` is chosen because it has **no dependencies**. That is not a detail: a
remote that fetches a single package does not serve anyone else's. Try with a
package that has some, and `pip` will list all its versions from your index
perfectly, then fail on `ResolutionImpossible`: the repository serves, but
not enough to resolve.

In production, a remote's `includes` list must therefore cover the **whole
dependency tree**, or not be limited at all.

## Why the last point is the only one that proves anything

A proxy that has cached nothing works perfectly as long as the Internet
answers: it relays. It is then **indistinguishable** from a real cache, and
you will find out the difference the day PyPI goes down, which is to say at
the worst possible moment. The only proof of a cache is to **take its source
away** and see it serve anyway.

That is what the validation does: it cuts outbound access to PyPI on
`depot.lab`, runs the installation again from `client.lab`, and restores it
afterwards.

## What is checked

- the remote exists, targets PyPI, and syncs only a named package;
- the repository has a synced version that actually holds content;
- the distribution answers, and its index is readable;
- `pip install` succeeds from `client.lab` through the repository;
- **the same installation still succeeds once PyPI is unreachable**;
- nothing relies on a package already present on the client: the virtual
  environment is new.

## Hints

- `pulp python remote create --help` shows the option that limits syncing to a
  list of packages.
- A sync is a **task**: `pulp task list` tells you where it stands.
- The address of the index served by the distribution ends with `/simple/`.
- On the client side, `pip install --index-url` is enough: nothing to
  configure globally.
