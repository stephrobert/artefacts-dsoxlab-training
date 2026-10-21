# The repository nobody documented

The person who ran `depot.lab` has left the team. The Pulp instance is up,
and that is about all the good one can say about it.

**Every build still reaches the public internet**: each `pip install` on each
machine fetches from PyPI, and the day PyPI answers badly the whole chain
stops. **In-house libraries** travel by email and file copy, with no version
and no traceability. **Container images** are pulled straight from Docker
Hub, pull quota included.

You take the repository over on Monday. You are asked to put the **three
chains** in place and to **prove** each one serves, because a configuration
that exists proves nothing about a service that answers.

This is an **exam**. Nothing will be explained a second time: the level's
four labs taught it, this one measures it. **Seven graded tasks**, **70
points** to pass, and everything is graded on the **real state of the
instance**, checked from `client.lab`, that is, from a machine that is not
the repository.

The instance credentials are the ones you have used since the first lab, in
`~/.config/pulp/cli.toml`.

## Chain 1: public packages no longer go out directly (30 points)

1. A **proxy** repository named **`epreuve-cache`**, pointing at
   **`https://pypi.org/`**, synced, and exposed by a **distribution** of the
   same name. *(15 points)*

2. Its **cache filled**: at least one package actually stored, after a client
   has gone through it. A proxy repository that keeps nothing is a detour, not
   a cache. *(15 points)*

## Chain 2: in-house libraries are hosted (40 points)

3. A Python package **built on `depot.lab`**, named **`epreuve-outil-n1`**,
   version **`1.0.0`**, and **uploaded** into a repository named
   **`epreuve-interne`**. That name exists on no public index: that is
   deliberate, and it is what makes the proof indisputable. *(10 points)*

4. A **distribution** named **`epreuve-interne`** whose index lists that
   package. *(10 points)*

5. From `client.lab`, in a **fresh** virtual environment, a
   `pip install epreuve-outil-n1` that **succeeds** through your repository,
   and a module that then **imports**. A package that installs but does not
   import has proven nothing. *(20 points)*

## Chain 3: images go through the repository (30 points)

6. A **container** repository serving Docker Hub images, exposed under the
   base path **`epreuve-images`**. *(15 points)*

7. From `client.lab`, an **image pull** that succeeds **through your
   repository**, not from Docker Hub. *(15 points)*

## What will not be forgiven

- A repository **with no distribution**: it is served to nobody, and no test
  will find it.
- A package uploaded **without a relative path**: Pulp accepts the file and
  the index does not offer it.
- A proof made **from the repository itself**: that machine hosts everything,
  it would succeed without anything being served. Every consumption check
  starts from `client.lab`.
- An **approximate name**. The seven names in this brief are exact, down to
  the hyphen.

## How you will know where you stand

```bash
dsoxlab check artefacts-epreuve-n1
```

Every check that passes awards its points. You need **70**.
