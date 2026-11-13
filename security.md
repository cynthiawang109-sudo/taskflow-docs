# TaskFlow — security

The standing rules that keep user data contained. Anything here that
conflicts with another document is a finding — raise it, don't pick a
side silently.

## Data classification

- Email addresses are the only PII in the system and live only in the
  `users` table (see `taskflow-api-docs`, `data-model.md`).
- Logs, metrics, traces, and support tooling work with user IDs only
  (see `observability.md`). No endpoint accepts a raw email address as
  a lookup key in a URL.

## Secrets

- Per-service, per-environment credentials live in the secrets
  manager — never in repositories, images, or CI variables that print
  to logs.
- Rotation is quarterly, and immediately on any suspected leak; the
  order of operations for a leak is in `incident-runbook.md`
  ("Suspected data leak in logs").

## Build and dependencies

- CI runs a dependency vulnerability scan on every merge, alongside
  the tests, lint, and container build in `deployment.md`. A critical
  finding blocks promotion to `prod`.
- Container images are pinned by digest, so a release is exactly the
  artifact CI built.

## Application rules

- All input is validated at the `api-service` boundary. Validation
  failures return `422` — code `validation_error`, or a more specific
  code where the catalog assigns one (for example `invalid_status`) —
  and error messages never echo submitted values back to the caller
  (see `taskflow-api-docs`, `errors.md`).
- Rate limiting is enforced per credential class
  (see `taskflow-api-docs`, `rate-limiting.md`).
- Deletes are soft and ownership transfer is audited
  (see `taskflow-api-docs`, `data-model.md`).

## Review requirements

- Any change touching authentication, token handling, or PII needs a
  second reviewer who was not the author.
- Any new table holding user-generated content states its PII story in
  `data-model.md` before its migration is approved.
