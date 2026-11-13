# TaskFlow — environments

Expands the environment table in `deployment.md` with the data,
secrets, and access rules for each environment. Release mechanics
themselves live in `deployment.md`; this file is about what may live
where.

| | `dev` | `staging` | `prod` |
|---|---|---|---|
| Data | Synthetic seed data | Anonymized snapshot of prod | Real data |
| Snapshot refresh | On demand (`make seed`) | Monthly, as a restore drill | — |
| Secrets | Local file outside the repo | Secrets manager, staging scope | Secrets manager, prod scope |
| Who can deploy | The developer | Any engineer | Manual pipeline approval (`deployment.md`) |
| Direct DB writes | Yes | Migrations only | Migrations only |

## Data rules

- Production data never enters `dev`. Debugging against real data
  happens in `prod` tooling with user IDs, or not at all.
- Anonymization for `staging` rewrites every `users.email` to a
  `@example.invalid` address and re-keys display names, before the
  snapshot is usable. Email remains the only PII column, so it is the
  only column the anonymizer touches.
- `staging` sends no real email: the worker's mail sink is a local
  outbox file, the same pattern the demo implementation uses.

## Configuration rules

- Configuration comes from environment variables; the same container
  image runs in every environment.
- A required variable missing in `prod` fails startup — fail closed,
  never fall back to a default credential or endpoint.
- Feature flags default to off in `prod`. A flag older than 90 days is
  a cleanup finding in review.
