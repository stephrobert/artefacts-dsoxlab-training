# Serve container images, and prove they come from your registry

The team's builds pull their base images from Docker Hub. Twice this month,
the download limit broke the chain in the middle of the day. You are asked to
serve those images from your own repository.

## What you must achieve

1. **Token authentication** enabled on Pulp. Without it the registry API does
   not work: `/v2/` must answer **401**, not 500.

2. A **pull-through remote** to Docker Hub, named `dockerhub`.

3. A **pull-through distribution** exposing it under the `dockerhub` path.

4. From `client.lab`, a `podman pull` that **succeeds through your
   repository** for a public image.

5. The pulled image must **carry your repository's address**: that is the
   proof it did not come straight from Docker Hub.

## The trap, and it is real

Supplying your own `settings.py` stops the Pulp image from generating the
default token settings. `/v2/` then answers **500** with `AttributeError:
TOKEN_SERVER` in the logs. A 500 looks like an outage: it is an incomplete
configuration. You must declare `TOKEN_SERVER`,
`TOKEN_SIGNATURE_ALGORITHM`, `PUBLIC_KEY_PATH` and `PRIVATE_KEY_PATH`, then
**generate the key pair** and restart the container.

## What is checked

- `/v2/` answers **401**: the token is active and correctly configured;
- the pull-through remote exists and targets the Docker registry;
- the distribution exists under the expected path;
- from `client.lab`, `podman pull` succeeds through the repository;
- the image present locally carries **the repository's address**, not
  `docker.io`.

## Hints

- Token settings go in the same `settings.py` as `CONTENT_ORIGIN`, and the
  container must **restart** to read them.
- The key pair is generated with `openssl ecparam -genkey -name prime256v1`.
- The pull-through remote and distribution are created through the **REST
  API**: the CLI does not expose them yet.
- Over HTTP, `podman` needs `--tls-verify=false`.
