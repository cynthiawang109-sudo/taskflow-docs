# ADR-0003: RQ for background jobs, over Celery

Status: accepted.

## Context

The `worker` runs email digests, webhook delivery, and report
generation. Redis is already in the stack for queues and board
presence (see `../system-overview.md`), and the job volume is modest:
bursts around digest time, a steady trickle of webhooks.

## Decision

Background jobs run on RQ over Redis. Retry policy is a workspace
convention, implemented the same way for every job type: exponential
backoff, dead-letter after 5 attempts (see `../incident-runbook.md`).

## Alternatives considered

- **Celery** — more routing and configuration surface than this
  workload needs, and a second operational model (broker, result
  backend, flower) for a three-job-type system.
- **Hand-rolled Redis lists** — retry, backoff, and dead-letter
  semantics would be reinvented per job type, which is how they drift
  apart.

## Consequences

- Scaling the worker means running more worker processes; there is no
  separate broker to operate.
- Job payloads stay small and ID-based (see `../architecture.md`),
  because RQ stores them in Redis.
- If job volume or routing needs outgrow RQ, this ADR is the document
  to supersede — the queue boundary is the one place that change
  would land.
