# TaskFlow — backup and recovery

## PostgreSQL

- Continuous WAL archiving with a point-in-time recovery window of
  7 days, plus a daily base backup. Backups are retained for 30 days,
  encrypted at rest, and copied to a second region.
- Targets: RPO 5 minutes (from WAL), RTO 1 hour for a primary restore.
- A restore is the recovery path once a migration's "contract" step
  has shipped (see `deployment.md`): at that point rollback stops
  being an option and restore takes over.

## Restore drills

- The monthly staging refresh (see `deployment.md`) is performed as a
  restore — latest base backup plus WAL replay — so the drill and the
  snapshot are the same event, and restores are practiced on real
  data shapes (anonymized on the way in, per `environments.md`).
- The drill result is recorded in the ops log. A failed drill is a
  severity-3 incident (see `incident-runbook.md`).

## Redis

- Redis runs with AOF persistence (`everysec`), which bounds queue
  loss on a crash. No separate Redis backups are kept: presence is
  ephemeral by design, and queued work is either processed or lands in
  a dead-letter list — which is why the runbook forbids purging the
  queue during an incident (see `incident-runbook.md`).

## Out of scope

- The demo implementation's SQLite file is fictional data on a
  developer's own machine and is explicitly not backed up
  (see `taskflow-api-docs`, `data-model.md`, "Demo implementation
  note").
