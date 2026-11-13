# TaskFlow — observability

What each service emits, and which signals page a human. The rule that
shapes everything below: logs, metrics, and traces carry user IDs,
never email addresses — PII in logs is a severity-1 incident
(see `incident-runbook.md`).

## Logs

- Structured JSON to stdout, shipped centrally; stopping that shipping
  is step one of the log-leak runbook procedure.
- Required fields: `ts`, `service`, `level`, `request_id`, and
  `user_id` when a user context exists.
- `request_id` is minted at the edge and propagated into worker job
  payloads, so one user action can be followed across `api-service`,
  the queue, and `worker`.

## Metrics

- Per endpoint: request rate, error rate split by the error `code`
  values in `taskflow-api-docs` (`errors.md`), and duration
  p50/p95/p99.
- Per queue: depth, oldest job age, and dead-letter list size.
- PostgreSQL: connection count, replica lag, and queries slower than
  500 ms.

## Traces

- OpenTelemetry spans in `api-service` for PostgreSQL queries and
  Redis enqueues; `worker` spans link back through `request_id`.
- Traces sample at 10% normally and 100% for requests that end in a
  5xx, so failures are always traceable after the fact.

## Alerts

| Signal | Threshold | Response |
|---|---|---|
| `/health` reports `degraded` | 2 minutes | Page on-call |
| Dead-letter list size | > 0 for 10 minutes | Page on-call (poison job — `incident-runbook.md`) |
| Replica lag | > 30 s for 5 minutes | Ticket, next business day |
| p99 latency on task list | > 800 ms for 15 minutes | Ticket, next business day |

Every paging alert names its runbook section. An alert without a
runbook entry is a review finding, not a nuisance to silence.
