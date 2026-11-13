# TaskFlow — architecture

How the components in `system-overview.md` interact at runtime, and why
the boundaries sit where they do.

## Request lifecycle (synchronous)

1. The browser (`web-app`) sends a REST call to `api-service` with a
   bearer token.
2. `api-service` validates the token, applies the business rules, and
   reads/writes PostgreSQL (the primary).
3. Side-effect work (notifications, webhooks, digests) is enqueued to
   Redis as part of the request, so email and webhook latency never sit
   on the request path.

## Asynchronous work

- `worker` consumes RQ queues on Redis. Job payloads carry IDs, never
  PII: the worker resolves what it needs (for example a digest
  recipient's email) from the database read-replica at run time.
- A failed job retries with exponential backoff and lands in a
  dead-letter list after 5 attempts (see `incident-runbook.md`).
- Report generation reads the read-replica, never the primary, so a
  heavy report cannot starve the request path.

## Realtime board presence

Presence (who is viewing a board, cursor positions) runs over Redis
pub/sub channels scoped per project. It is ephemeral by design: nothing
is persisted, and a Redis restart costs presence only, never data.

## Scaling posture

- `api-service` is stateless; scale it horizontally. All shared state
  lives in PostgreSQL and Redis.
- One PostgreSQL primary, one read-replica. Because `api-service` is
  the only writer (see `system-overview.md`), the write path stays
  auditable.
- The hot read path is the board list, which is why list endpoints use
  cursor pagination backed by a `(project_id, status, id)` index
  (see ADR-0002 and `taskflow-api-docs`, `data-model.md`).

## Failure domains

| Failure | Effect | First move |
|---|---|---|
| PostgreSQL primary down | `/health` reports `db: down`; writes and most reads fail | `incident-runbook.md`, "API returning 5xx" |
| Redis down | Queues and presence stop; API reads still serve | Restart Redis; expect queued work to resume, presence to rebuild |
| `worker` down | Queue depth grows; digests and webhooks delayed | `incident-runbook.md`, "Worker queue backing up" |
| Read-replica lag | Worker and reports read stale data | Alert at 30 s lag (see `observability.md`) |
