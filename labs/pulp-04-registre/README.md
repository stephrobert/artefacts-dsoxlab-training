# pulp-04-registre

**Audience:** the learner.

Turn the repository into an image registry, and prove the images pulled
really come from it.

## What you will be able to do

- Enable **token authentication**, without which the registry API does not
  work.
- Create a **pull-through cache** to a public registry.
- **Pull an image** through the repository from another machine.
- Check that an image came from the repository, not from the public
  registry.

## Duration

About 40 minutes.

## The trap, and it is expensive

Supplying your own `settings.py` stops Pulp from generating the default token
settings. `/v2/` then answers **500** with `AttributeError: TOKEN_SERVER`. A
500 looks like an outage: it is an incomplete configuration. Five settings, a
key pair, one restart.

## A validation detail

The pull-through remote and distribution are created through the **REST
API**: the CLI does not expose them yet.
