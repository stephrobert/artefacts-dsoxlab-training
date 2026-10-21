# artefacts-epreuve-n1

**Audience:** the learner who has finished the level's four labs.

End-of-level exam. Seven graded tasks, 100 points, 70 to pass. Nothing is
explained a second time, and no hints are provided.

## What it measures

- Putting a proxy repository into service and proving its cache fills.
- Hosting an in-house package, exposing it, and having it installed from
  another machine.
- Serving container images through the repository.

Every consumption check starts from `client.lab`: the repository hosts
everything, and an install run from it would succeed without anything being
served.

## What it does not touch

The level's four lab repositories. It requires its own objects, prefixed
`epreuve-`, and its checks look only at those.
