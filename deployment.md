# TaskFlow — deployment

## Environments

| Environment | Purpose | Data |
|---|---|---|
| `dev` | Per-developer sandbox | Synthetic seed data |
| `staging` | Pre-release verification | Anonymized snapshot, refreshed monthly |
| `prod` | Live service | Real data |

## Release mechanics

1. Merge to `main` triggers CI: tests, lint, container build.
2. The release-assistant checklist (sibling repo `release-assistant`) must be
   completed for any `prod` promotion.
3. Promotion is a manual approval on the CI pipeline — never automatic.
4. Database migrations run *before* the new container starts, and must be
   backward-compatible with the previous release (expand → migrate →
   contract). A migration that drops a column ships in two releases.

## Rollback

- Application rollback: redeploy the previous container tag; takes effect in
  under 5 minutes.
- Migration rollback: only the "expand" step is freely reversible. Once the
  "contract" step has shipped, restore from backup instead — see
  `incident-runbook.md`.
