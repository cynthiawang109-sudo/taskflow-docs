# ADR-0002: Cursor pagination for all list endpoints

Status: accepted.

## Context

The board is the product's hot path, and it is a moving target: while
a client pages through a column, other users create, complete, and
reorder tasks. Offset pagination skips or repeats rows under exactly
that concurrent-write pattern, which users experience as tasks
vanishing or appearing twice.

## Decision

All list endpoints use keyset (cursor) pagination: an opaque cursor,
a default page size of 50, a maximum of 200, and `next_cursor` set to
`null` at the end of a list. The full contract is in
`taskflow-api-docs`, `api-conventions.md`.

Board queries are backed by a `(project_id, status, id)` index so a
page is an index range scan, not a sort.

## Consequences

- Clients cannot jump to "page N". Accepted: boards are streams, not
  documents, and no client has needed random access.
- Cursors are opaque and forgiving — out-of-range values are clamped,
  never an error, so a paging client cannot wedge itself.
- New list endpoints inherit the rule; an offset-paginated endpoint is
  a review finding.
