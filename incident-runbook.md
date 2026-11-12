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

## Suspected data leak in logs

1. Stop the affected service's log shipping first, then rotate its tokens.
2. Search shipped logs for email patterns; PII in logs is a severity-1 by
   policy (see `system-overview.md`, "Boundaries and rules").
