# pulp-05-securiser

**Audience:** the learner.

Give an account the right to do one thing, and prove it cannot do others.

## What you will be able to do

- Create a **limited account** on Pulp.
- Grant it a **targeted role**, globally.
- Check that a granted right **opens one door** and only one.

## Duration

About 30 minutes.

## What writing this lab taught

Its first version asked for a "read-only" account. Measured on the instance:
**a fresh Pulp account, with no role at all, already reads the catalog and is
refused writes.** The test was green without anyone granting anything.

In Pulp you do not take rights away: you add them. The proof of a well-set
role is one door open **and** the others still shut.

## One detail that costs ten minutes

A global role is granted with **`--object ""`**. Without it the CLI answers
`--object must be set when not using --domain`, and the assignment fails
silently if you do not read its output.
