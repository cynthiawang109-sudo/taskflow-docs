# taskflow-docs

System documentation for **TaskFlow**, a fictional project-management SaaS.
This repository is the source of truth for how TaskFlow is built and operated;
other workspace projects (code-reviewer, release-assistant) read it but never
modify it as a side effect of their own work.

Part of [ai-workspace-kit](https://github.com/cynthiawang109-sudo/ai-workspace-kit).
All content is original and fictional.

## Contents

| File | What it covers |
|---|---|
| `system-overview.md` | Components, data flow, and the boundaries between services |
| `deployment.md` | Environments, release mechanics, rollback |
| `incident-runbook.md` | First-response steps for the common failure modes |
| `architecture.md` | Request lifecycle, async work, scaling, failure domains |
| `authentication.md` | Sessions, API tokens, service-to-service auth, admin MFA |
| `observability.md` | Logs, metrics, traces, and the alerts that page |
| `security.md` | PII rules, secrets, dependency policy, review requirements |
| `environments.md` | Per-environment data, secrets, and access rules |
| `backup-and-recovery.md` | PostgreSQL backups, PITR, restore drills |
| `adr/` | Architecture decision records (PostgreSQL, cursor pagination, RQ) |

API-level contracts (endpoints, payloads, data model) live in the sibling
repo `taskflow-api-docs`.
