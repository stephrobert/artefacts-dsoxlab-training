# nexus-01-proxy

**Audience:** the learner.

This lab puts a Nexus Repository into service in front of PyPI, and serves
both the public index and your in-house packages from a single URL.

## What you will be able to do

- Accept the Community Edition EULA through the REST API, and recognise the
  403 it causes on every download until then.
- Change the throwaway password Nexus generates on first startup, and know
  where it is written.
- Create proxy, hosted and group repositories through the REST API.
- Understand what a group repository is, why Pulp has no equivalent, and why
  member order protects against dependency confusion.
- Check a cache actually filled, rather than merely being configured.

## What this lab assumes

Lab `pulp-02-proxy`: the same job with Pulp, which this one compares itself
to throughout. This lab runs on `nexus.lab`, a machine separate from Pulp's.
