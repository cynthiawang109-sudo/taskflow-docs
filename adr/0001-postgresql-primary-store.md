# ADR-0001: PostgreSQL as the primary store

Status: accepted.

## Context

Projects, tasks, and comments are relational data with invariants an
engineer must be able to state in one breath: a project has exactly
one owner, a task's status transition to `done` sets `completed_at`
in the same transaction, comments are append-only. Board queries need
ordered, filtered scans over those relations.

## Decision

PostgreSQL 16 is the single primary store for users, projects, tasks,
and comments. `api-service` is its only writer (see
`../system-overview.md`); everything else reads the read-replica or
the queue.

## Alternatives considered

- **MongoDB** — the invariants would move into application code, where
  they are easier to bypass and harder to review.
- **MySQL** — workable, but weaker support for the partial indexes and
  transactional DDL the migration style in `../deployment.md` relies
  on.
- **SQLite** — single-writer and file-local; right for the demo
  implementation, wrong for a multi-instance service.

## Consequences

- One store to back up, with point-in-time recovery (see
  `../backup-and-recovery.md`).
- Schema changes follow the expand → migrate → contract discipline;
  there is no schemaless escape hatch.
- Reporting and worker reads go to the replica, so their load never
  contends with the write path.
