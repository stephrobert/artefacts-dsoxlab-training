# Publish your own package, and install it from another machine

The repository now serves public packages. The team also has its own
libraries, which travel today by file copy and email. You are asked to
**host** them in Pulp.

## What you must achieve

1. A Python package **built on `depot.lab`**, named **`outils-maison-lab`**,
   at version **`1.0.0`**. That name exists in no public repository: this is
   deliberate, and it is what will make the proof airtight.

2. That package **uploaded into Pulp** and present in a repository named
   **`interne`**.

3. A **distribution** named **`interne`** exposing it.

4. From `client.lab`, a `pip install outils-maison-lab` that **succeeds**
   through your repository, in a fresh virtual environment.

## Why the name matters

If the lab had you publish a package that exists on PyPI, the installation
could succeed **without your repository serving any purpose**: pip would
fetch it elsewhere. With a name that exists nowhere, a successful install
proves the package came from you.

## What is checked

- the `interne` repository exists and holds a **non-empty** version;
- the uploaded content carries the requested name and version;
- the distribution answers, and its index lists the package;
- from `client.lab`, the install succeeds **in a fresh environment**;
- the module actually **imports** after installation: a package that
  installs but does not import has proven nothing.

## Hints

- `python3 -m build` produces a distribution in `dist/`.
- `pulp python content upload --help` shows how to upload a file and add it
  to a repository in one go.
- A `python` repository accepts uploaded packages as well as synced ones.
