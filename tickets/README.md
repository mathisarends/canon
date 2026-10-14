# Hardening tickets

Findings from the production-readiness review covering connection
loss, retries, timeouts, and related edge cases. **One ticket is one PR.** Each
ticket bundles the findings that touch the same code and belong together, and
is self-contained so an agent can implement it without further context.
Checked against `personal/main` at `051440e` on 2026-10-12. Reproduce each
finding against the implementation branch before changing code; names and
behaviour may change as earlier tickets land.

Work through them in the order below. A ticket lists its prerequisites under
**Depends on**; do not start it before those are merged.

## Rules for every ticket

- Read `AGENTS.md` first and follow its conventions.
- Client runtime changes go into the templates under
  `rpckit/codegen/templates/{python,typescript}/`, never into generated output
  directly. After a template change, regenerate the examples with
  `uv run rpckit generate --config examples/generated_clients/rpcgen.toml`;
  `tests/test_examples.py` checks they match.
- When a ticket touches client behaviour, change **both** the Python and the
  TypeScript client unless the ticket says otherwise. Keep them behaviourally
  equivalent.
- Every bug fix comes with a regression test that fails before the fix.
  Server tests mirror the package (`tests/test_*.py`); generated-client tests
  live in `tests/codegen/`. Once ticket 03 is merged, prefer its
  fault-injecting sockets for resilience tests.
- Use events, barriers, and controlled timers for concurrency tests. Assert
  that cleanup leaves no pending futures, tasks, timers, or listeners.
- Preserve Python cancellation (`asyncio.CancelledError`) and TypeScript
  abort semantics. Do not wrap caller cancellation as a transport failure or
  retry it. Normalize failures caused by the transport itself.
- Defaults for new retry, heartbeat, deadline, and reconnect features must
  state their compatibility impact. Treat proposed API names as suggestions;
  keep the agreed wire conventions consistent across dependent tickets.
- Update the relevant guide in `docs/` when public behaviour or API changes,
  and add an entry to `CHANGELOG.md`.
- Run `uv run ruff check .`, `uv run ruff format --check .`, and
  `uv run pytest` before opening the PR (use `uv run ruff format .` to fix
  formatting). Run `uv run python scripts/verify_types.py` for public Python
  API changes. For TS changes, ensure Node.js and npx are available and the
  relevant runtime, strict type-checking, and formatting tests actually run;
  report skipped checks explicitly.
- When the ticket is done, set its **Status** to `done` and link the PR.

## Order

| # | Ticket | Area | Priority | Depends on |
|---|--------|------|----------|------------|
| 01 | [Client transport correctness](01-client-transport-correctness.md) | client | critical | – |
| 02 | [Server input hardening](02-server-input-hardening.md) | server | high | – |
| 15 | [Pending accounting and capacity limits](15-server-capacity-limits.md) | server + docs | high | – |
| 03 | [Fault-injecting sockets for resilience tests](03-fault-injection-testing.md) | testing | high | – |
| 04 | [Client error taxonomy](04-client-error-taxonomy.md) | client | high | 01 |
| 05 | [Server request deadlines and cancellation](05-server-deadlines-and-cancellation.md) | server | high | 01, 15 |
| 06 | [Client request cancellation](06-client-request-cancellation.md) | client | high | 04, 05 |
| 07 | [Reconnect policy and connection state](07-reconnect-policy-and-state.md) | client | high | 04 |
| 08 | [Notifications across reconnects](08-notifications-across-reconnects.md) | client | high | 07 |
| 09 | [Dead-connection detection in the TypeScript client](09-ts-dead-connection-detection.md) | client (TS) | high | 05, 07 |
| 10 | [Idempotent methods and automatic retry](10-idempotent-methods-retry.md) | contract + client | medium | 04, 07 |
| 11 | [Graceful drain on shutdown](11-graceful-drain.md) | server | high | 05, 07 |
| 12 | [Credential expiry on long-lived connections](12-credential-expiry.md) | server + docs | medium | 07 |
| 13 | [Client hooks for errors and per-call state](13-client-hooks.md) | client | medium | 04 |
| 14 | [Per-request trace context propagation](14-per-request-trace-context.md) | server + client | medium | 13 |

Ticket numbers are stable identifiers; the table gives implementation order.
Tickets 01, 02, 03, and 15 are independent. Ticket 03 is recommended test
infrastructure for the later resilience work, rather than a mandatory dependency.

## Implementation progress

The current PRs are stacked in implementation order. Each PR targets the preceding
branch and includes its SDK impact, rationale, validation, and changelog update.
Merge the stack from the bottom up; subsequent PR descriptions link their base.

| Ticket | Status | PR | Builds on |
|--------|--------|----|-----------|
| 01 | done | [#23](https://github.com/mathisarends/pyrpckit/pull/23) | main |
| 02 | done | [#24](https://github.com/mathisarends/pyrpckit/pull/24) | #23 |
| 15 | done | [#25](https://github.com/mathisarends/pyrpckit/pull/25) | #24 |
| 03 | done | [#26](https://github.com/mathisarends/pyrpckit/pull/26) | #25 |
| 04 | done | [#27](https://github.com/mathisarends/pyrpckit/pull/27) | #26 |
| 05 | done | [#28](https://github.com/mathisarends/pyrpckit/pull/28) | #27 |
| 06 | done | [#29](https://github.com/mathisarends/pyrpckit/pull/29) | #28 |
| 07 | done | [#30](https://github.com/mathisarends/pyrpckit/pull/30) | #29 |
| 08 | done | [#31](https://github.com/mathisarends/pyrpckit/pull/31) | #30 |
| 09 | done | [#32](https://github.com/mathisarends/pyrpckit/pull/32) | #31 |
| 10 | done | [#33](https://github.com/mathisarends/pyrpckit/pull/33) | #32 |

Tickets 11–14 remain open. Ticket 11 is next and can build on #33. Review and
merge prerequisite PRs before merging the dependent work.

## Review coverage

The later numbered findings are grouped as follows; the earlier findings
are described directly in the problem sections of the tickets.

| Review finding | Ticket |
|----------------|--------|
| 14: error hooks and request tracing | 13, 14 |
| 15: send outside the client timeout | 01 |
| 16: client-triggered log flooding | 02 |
| 17: batch accounting and server-wide limits | 15 |
| 18: transport frame-size limit | 15 |
| 19: notification overflow visibility | 08 |
| 20: notification hub retention | 08 |
| 21: static transport close failures | 01 |
