# TaskFlow — authentication

How users, integrations, and services prove who they are. Authorization
(which project a user may touch) is enforced in `api-service` on every
request, on top of the identities established here.

## User sessions (web-app)

- Login issues a short-lived access token (JWT, 15 minutes), presented
  to `api-service` as a bearer token — the only credential the browser
  sends, per `system-overview.md`.
- The refresh token lives in an `HttpOnly`, `Secure`, `SameSite=Lax`
  cookie, is rotated on every refresh, and expires absolutely after
  30 days.
- Logout revokes the refresh token server-side; revoked tokens are kept
  on a Redis deny-list until they would have expired anyway.

## Passwords

- Stored with argon2id; checked against a breached-password corpus at
  set and reset time.
- Password reset uses a single-use emailed link (1 hour). The email is
  sent by `worker`; the link carries a token hash, never the email
  address or user ID in clear text beyond what the link needs.

## API tokens (integrations)

- Created per user from the settings UI; shown exactly once; only a
  SHA-256 hash is stored.
- Scoped `read` or `write`, and rate-limited as their own class
  (see `taskflow-api-docs`, `rate-limiting.md`). Tokens carry the
  prefix `tf_live_` so logs and tooling can tell the credential class
  apart without seeing the secret.
- Revocation is immediate and is the first step when a token leaks
  (see `security.md`).

## Service-to-service

- `worker` never calls the public API of `api-service` (a standing
  boundary in `system-overview.md`); it authenticates to the PostgreSQL
  read-replica and to Redis with per-service credentials from the
  secrets manager (see `security.md`).
- The only unauthenticated endpoint anywhere is `GET /health`, which by
  contract reveals nothing beyond check names
  (see `taskflow-api-docs`, `api-conventions.md`).

## Admin access

- Administrative actions (including project ownership transfer, an
  audited action per `taskflow-api-docs`, `data-model.md`) require a
  fresh MFA challenge (TOTP or WebAuthn) in addition to a live session.
