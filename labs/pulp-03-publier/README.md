# pulp-03-publier

**Audience:** the learner.

Host a package your team produces in Pulp, and install it from another
machine.

## What you will be able to do

- Build a **Python distribution** from a `pyproject.toml`.
- **Upload** a package into Pulp and add it to a repository.
- **Expose** it through a distribution.
- **Install it from another host**, in a fresh environment.

## Duration

About 35 minutes.

## What you are given

The Pulp instance from the first lab, the build tools on the repository side,
and what it takes to install on the client side.

## Why the package name is made up

`outils-maison-lab` exists in no public repository. Had the lab you publish a
well-known package, the install could succeed without your repository serving
any purpose: pip would fetch it elsewhere. Here, success proves the package
came from you.

## One detail that costs ten minutes

`pulp python content create` (which replaces `content upload`, deprecated since
pulp-cli 0.38.0) requires **`--relative-path`**, the name the
file will be served under. Without it the command refuses, and the message
only says so by printing its usage.
