# v0.0.1 release review tickets

These tickets describe reproduced defects found during the October 17, 2026
release review. They are implementation tasks, not completed fixes.

Baseline: commit `02d138b` on `main`. The existing suite passed: **125 Python
tests and 16 TypeScript tests**. Additional targeted probes exposed the defects
below, so passing the existing suite alone does not resolve these tickets.

| Ticket | Priority | Problem | Suggested integration order |
| --- | --- | --- | --- |
| [001](001-stream-response-contract-consistency.md) | P1 | Response serialization options break the generated stream contract | Independent |
| [002](002-python-generated-field-name-collisions.md) | P2 | Valid optional field names make generated Python packages fail to import | Before 004 |
| [003](003-typescript-nullable-parameter-serialization.md) | P2 | TypeScript serializes optional nullable parameters as the string `null` | Independent |
| [004](004-python-additional-properties-policy.md) | P2 | Generated Python models ignore explicit `additionalProperties: false` | After 002 |
| [005](005-ref-sibling-constraints.md) | P2 | Schema restrictions alongside `$ref` silently disappear | After 004 |
| [006](006-required-properties-without-property-definitions.md) | P2 | Required keys without entries in `properties` disappear | After 005 |

P1 should block the release. P2 tickets should be fixed, or their unsupported
input explicitly rejected, before advertising that input as supported in
v0.0.1. Tickets 001–003 affect ordinary FastAPI usage. Ticket 004 also affects
ordinary Pydantic models configured with `extra="forbid"`. Tickets 005–006 are
especially relevant to custom or externally supplied OpenAPI contracts.

## Instructions for implementation agents

- Read the repository's `AGENTS.md` and the complete ticket before editing.
- Update generators and templates; never patch generated clients by hand.
- Add regression tests that demonstrate the reported behavior, then implement
  the fix. Keep wire names and existing public behavior stable unless the ticket
  explicitly calls for rejecting unsupported input.
- Use the proposed approach as guidance. A different implementation is acceptable
  if it meets the acceptance criteria and preserves the documented scope.
- Tickets 002 and 004 touch the Python model generator; tickets 004–006 can touch
  the shared IR. The integration order above avoids overlapping changes in those
  files. Parallel work should use isolated checkouts and account for those changes.
- Keep public Python classes/functions above private implementation helpers.
- If generator output changes, regenerate committed artifacts with
  `uv run python scripts/codegen.py` and review the diff.
- At completion, record the implementation, commands run, results, and any scope
  limitation in the ticket. Do not mark a ticket complete based only on the
  pre-existing tests passing.

## Validation

Start with each ticket's focused tests, then run the applicable repository checks:

```sh
uv run pytest -q
npm test
npm run typecheck
uv run pyright
uv run ruff check .
uv run ruff format --check .
uv run python scripts/codegen.py --check
```

Follow `docs/development.md` for the full release validation, including coverage,
compatibility, and package smoke tests when relevant. Generated runtime changes
must be exercised with both supported Python HTTP backends where applicable.

The review's initial sandboxed Windows runs could not create pytest temporary
directories and blocked while creating asyncio's local socket pair. Running the
suite outside that sandbox completed successfully. Those environment failures
are not repository defects and should not prompt application-code workarounds.

The reproductions in these tickets are self-contained descriptions; do not rely
on the reviewer's untracked `.pytest_cache` probes being available.
