# TaskFlow — system overview

TaskFlow is a (fictional) project-management SaaS: teams create projects,
break them into tasks, and track work on boards. This document describes the
system at the level an engineer — or an AI assistant — needs before touching
code or reviewing a change.

## Components

| Component | Stack | Responsibility |
|---|---|---|
| `web-app` | Next.js / TypeScript | Browser UI, board rendering, realtime updates |
| `api-service` | FastAPI / Python | REST API, business rules, auth tokens — the demo implementation in this workspace is `demo-app` |
| `worker` | Python / RQ | Email digests, webhook delivery, report generation |
| `postgres` | PostgreSQL 16 | Primary store: users, projects, tasks, comments |
| `redis` | Redis 7 | Job queues, board presence, rate-limit counters |

## Data flow

1. The browser talks only to `api-service` (REST, JSON, bearer tokens).
2. `api-service` writes to PostgreSQL and enqueues side-effect work
   (notifications, webhooks) to Redis.
3. `worker` processes the queue; a failed job retries with backoff and lands
   in a dead-letter list after 5 attempts (see `incident-runbook.md`).
4. Board presence is ephemeral: Redis pub/sub, never persisted.

## Boundaries and rules

- `api-service` is the only component allowed to write to PostgreSQL.
- `worker` must never call the public API of `api-service`; it reads the
  database read-replica and the queue payload.
- Every service exposes a health endpoint per the contract in
  `taskflow-api-docs` (`api-conventions.md`, "Health checks").
- PII (email addresses) is stored only in the `users` table; logs must use
  user IDs, never raw emails.
