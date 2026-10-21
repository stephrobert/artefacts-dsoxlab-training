# Sign an image, and prove verification refuses an unsigned one

Your images are served by your registry. Nothing says, though, that an image
pulled today is the one you pushed yesterday: a compromised registry, a man
in the middle, a mistake, and nobody notices.

**Signing** means attaching cryptographic proof that an artifact comes from
you. **Verifying** means refusing whatever does not carry it.

## What you must achieve

1. A **Cosign key pair** on `client.lab`, in `/home/student/cosign.key` and
   `/home/student/cosign.pub`. The private key must not be world-readable.

2. **Two images pushed** into your registry, under the `interne` path:
   `interne/alpine:1.0` and `interne/busybox:1.0`.

3. **Only the first one is signed.**

4. Verification **succeeds** on the signed image, and **fails** on the other.

## Why you must PUSH the images, and not sign the cached ones

A Cosign signature is not a file on the side: it is **an object in the
registry**, pushed next to the image. The previous lab's *pull-through* cache
is **read-only**: it relays an upstream registry, it is not yours.

Try to sign an image there and you will get
`UNAUTHORIZED: Insufficient permissions`, a message that talks about rights
when the problem is one of **nature**: you only sign what you host.

## Why the refusal is the only test that gives the others their value

A `cosign verify` that succeeds proves nothing until you have seen what it
refuses. If it accepted everything, it would pass on the signed image in
exactly the same way, and you would have nothing but an illusion of control.

## What is checked

- the key pair exists, and the private key is **not world-readable**;
- both images are **present in the registry**, under `interne`;
- `cosign verify` **succeeds** on the signed image;
- `cosign verify` **fails** on the unsigned image;
- verification also fails with a **different key**: a signature is only worth
  the key that produced it.

## Hints

- `cosign generate-key-pair` asks for a passphrase; the `COSIGN_PASSWORD`
  variable supplies it without a prompt.
- Pushing an image creates the repository on the Pulp side: `podman push` is
  enough.
- Over HTTP, `cosign sign` and `cosign verify` take `--allow-http-registry`;
  `cosign login` does not know that option.
- With no transparency log, add `--tlog-upload=false` to the signature and
  `--insecure-ignore-tlog=true` to the verification.
