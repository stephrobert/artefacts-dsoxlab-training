# pulp-06-signer

**Audience:** the learner.

Sign an image hosted by your registry, and prove verification refuses what is
not signed.

## What you will be able to do

- Generate a **Cosign key pair** and protect the private one.
- **Push** images into your own repository.
- **Sign** an image, the signature being hosted by the registry.
- **Verify** a signature, and see what it refuses.

## Duration

About 35 minutes.

## What writing this lab taught

Its first version had you sign an image from the previous lab's
**pull-through cache**. `cosign sign` failed with `UNAUTHORIZED: Insufficient
permissions` — a message about rights when the problem is one of **nature**:
a Cosign signature is an **object in the registry**, pushed next to the
image, and a pull-through repository is **read-only**.

You only sign what you host. The lab therefore has you push two images into a
repository that is yours.

## Two details that cost time

- `cosign login` **does not know** `--allow-http-registry`; only `sign` and
  `verify` take it.
- With no transparency log, you need `--tlog-upload=false` when signing and
  `--insecure-ignore-tlog=true` when verifying.
