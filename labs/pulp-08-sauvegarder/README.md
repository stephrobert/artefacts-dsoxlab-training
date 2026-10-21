# pulp-08-sauvegarder

**Audience:** the learner.

This lab teaches how to back up the contents of a Pulp repository and, above
all, how to prove the restore actually serves a client.

## What you will be able to do

- Allow an export path and an import path in Pulp's configuration, and know
  those settings are only read at startup.
- Produce a repository export, and recognise its two inseparable files: the
  archive and its table of contents.
- Move a backup off the machine it protects.
- Run an import through the API, because the CLI cannot do it.
- Publish the restored repository and check a client installs from it.

## What this lab assumes

`pulp-01-installer` for the instance, and `pulp-03-publier` for the
`interne` repository that provides the material to back up.
