# TaskFlow — incident runbook (first response)

## API returning 5xx across the board

1. Check the `api-service` health endpoint (contract in `taskflow-api-docs`).
2. If health is `degraded` with `db: down`, check PostgreSQL primary status
   before restarting anything — restarts do not fix a down database.
3. If health is `degraded` with `task_store: down`, the api-service cannot
   reach its task store. Restart the api-service process. Task data lives
   in a local SQLite file and survives a restart; if health is still
   degraded afterwards, check that the database file (TASKFLOW_DB_PATH)
   exists and is readable before treating it as a code defect: roll back
   the last deploy.
4. If a deploy landed in the last 30 minutes, roll back first, investigate
   second (see `deployment.md`).

## Worker queue backing up

1. Read the dead-letter list size. A growing dead-letter list with a flat
   main queue means one poison job, not a capacity problem.
2. Move the poison job aside, note its payload ID in the incident ticket,
   and let the queue drain.
3. Do not purge the queue: webhook deliveries are not replayable from
   anywhere else.

## Digest job dead-lettered (demo store)

The digest ledger is the `digest_sends` table in the demo SQLite
database (`TASKFLOW_DB_PATH`).

1. Inspect the row:
   `SELECT user_id, week, status, attempts, last_error FROM digest_sends WHERE status = 'dead';`
   `last_error` is a sanitized error code (exception class name), not
   the raw failure — check the worker logs around the attempts for
   detail.
2. Before replaying, check the outbox for the idempotency key
   `user_id:week`: the failure may have happened after delivery. If
   the key is already there, do not reset — mark the row sent instead:
   `UPDATE digest_sends SET status = 'sent', sent_at = '<now>' WHERE user_id = '<id>' AND week = '<week>';`
3. If the key is not in the outbox, reset the row for a fresh run:
   `UPDATE digest_sends SET status = 'pending', attempts = 0, last_error = NULL WHERE user_id = '<id>' AND week = '<week>';`
4. Re-run the job (`scripts/run_digest.py --user <id> --week <week>`)
   and confirm the row lands on `sent`.

## Suspected data leak in logs

1. Stop the affected service's log shipping first, then rotate its tokens.
2. Search shipped logs for email patterns; PII in logs is a severity-1 by
   policy (see `system-overview.md`, "Boundaries and rules").
