# TaskFlow — incident runbook (first response)

## Severity levels

| Sev | Meaning | Examples | Response |
|---|---|---|---|
| 1 | Data risk or full outage | PII found in logs; API 5xx across the board | Page on-call; post comms every 30 minutes |
| 2 | A major function is degraded | Worker queue stalled; `/health` degraded on one dependency | Page on-call; post comms hourly |
| 3 | Minor or partial impact | One digest batch dead-lettered; a failed restore drill | Ticket; next business day |


## API returning 5xx across the board

1. Check the `api-service` health endpoint (contract in `taskflow-api-docs`).
2. If health is `degraded` with `db: down`, check PostgreSQL primary status
   before restarting anything — restarts do not fix a down database.
3. If health is `degraded` with `task_store: down`, the api-service cannot
   reach its task store. In production that store is PostgreSQL: check
   connectivity and credentials before restarting anything. In the demo
   implementation the store is a local SQLite file: restart the
   api-service process (the data survives a restart); if health is still
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

## Worker queue recovery (demo store)

The queue is the `jobs` table in the demo SQLite database
(`TASKFLOW_DB_PATH`).

1. Inspect jobs by status:
   `SELECT id, kind, status, attempts, last_error, next_attempt_at FROM jobs ORDER BY status, id;`
   To list only one status, add `WHERE status = 'running'` before
   `ORDER BY` (substitute `queued`, `done`, or `dead` as needed).
   `queued` means waiting for a worker, eligible once `next_attempt_at`
   is due; `running` means claimed by a worker, possibly interrupted;
   `done` means the handler completed; `dead` means the attempt limit
   was reached and automatic retries have stopped. Check worker logs
   for detail behind the sanitized exception class in `last_error`.
2. For jobs left `running` by a worker that stopped, first confirm that
   no other worker process is active. This is a hard prerequisite:
   recovery must only run when no other worker process is active.
   From the demo application directory, run `python scripts/run_worker.py`,
   which calls `recover_interrupted` at startup. Recovery counts each
   interruption as an attempt, sets `last_error` to `InterruptedError`,
   and returns the row to `queued` with the normal backoff
   (`min(2 ** attempts, 300)` seconds). At 5 attempts it marks the row
   `dead` instead. The script drains only currently due jobs; run it
   again after the backoff to process recovered rows, with the same
   no-other-worker prerequisite.
3. Before replaying a `weekly_digest` job, read its `payload` for the
   `(user_id, week)` pair and check the digest ledger:
   `SELECT user_id, week, status, attempts, last_error FROM digest_sends WHERE user_id = '<id>' AND week = '<week>';`
   An already-recorded send (`status = 'sent'`) is skipped by the digest
   handler, so replay does not double-send. If the ledger needs recovery,
   follow the adjacent digest procedure, including its outbox check.
4. Fix the underlying cause before resetting a dead job by hand. Prefer
   this only for the local demo database. With workers stopped, reset
   only the affected row:
   `UPDATE jobs SET status = 'queued', attempts = 0, last_error = NULL, next_attempt_at = 0 WHERE id = <job_id> AND status = 'dead';`
   Run `python scripts/run_worker.py` from the demo application directory
   and inspect the row again to confirm the outcome.

## Suspected data leak in logs

1. Stop the affected service's log shipping first, then rotate its tokens.
2. Search shipped logs for email patterns; PII in logs is a severity-1 by
   policy (see `system-overview.md`, "Boundaries and rules").

## Communications template

Post updates in the incident ticket and the status channel, on the
cadence the severity demands:

```
Status: investigating | identified | monitoring | resolved
Impact: <who and what is affected, in user terms>
Since: <UTC time the impact started>
Next update: <time; at most 30 minutes out for severity 1>
```

Refer to users by ID only, never by email (see `security.md`), and
keep the wording blameless: what happened, what it affects, what
happens next.
