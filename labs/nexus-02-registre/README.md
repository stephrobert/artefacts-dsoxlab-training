# nexus-02-registre

**Audience:** the learner.

This lab has Nexus host a container image registry, with the two settings
the installation does not provide: the connector on a dedicated port and the
token authentication realm.

## What you will be able to do

- Create a hosted Docker repository and attach an HTTP connector on its own
  port.
- Recognise the symptoms of a port the container does not publish and of an
  inactive realm, neither of which the error messages name.
- Declare a plain-HTTP registry in podman's configuration, and know why that
  only belongs in a lab.
- Push an image, then check on the Nexus side that it really is there.

## What this lab assumes

`nexus-01-proxy`, whose instance it reuses: the EULA is accepted there, the
`admin` password changed and written to `/home/student/.nexus-motdepasse`.
`pulp-04-registre` helps for comparison: with Pulp, the registry shares the
API's port and authentication.
