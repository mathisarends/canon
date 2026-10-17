# Canon

One workspace for the FastAPI application stack: architecture conventions,
feature composition and HTTP contracts, typed SSE, and WebSocket RPC.

Canon is the ecosystem; `fastapi-canon` is its application-composition package.
The libraries remain independently installable and independently versioned.

| Component | Location | Distribution / import |
| --- | --- | --- |
| Composition, Dishka, HTTP contracts | [`packages/fastapi-canon`](packages/fastapi-canon) | `fastapi-canon` / `fastapi_canon` |
| Typed SSE and generated clients | [`packages/fastapi-streams`](packages/fastapi-streams) | `fastapi-streams` / `fastapi_streams` |
| WebSocket RPC and generated clients | [`packages/websocket-rpc`](packages/websocket-rpc) | currently `pyrpckit` / `rpckit` |
| Architecture conventions | [`guides`](guides) | feature slices, inward dependencies, Dishka |
| Runnable architecture example | [`examples/reference-service`](examples/reference-service) | development-only workspace member |

The RPC directory is provisional. Its distribution, imports, CLI, and protocol
stay unchanged during consolidation. A distinct successor name and consumer
migration belong to a later milestone.

Read the [vision](VISION.md), the concrete [workspace decision](docs/design-decisions/0001-workspace.md),
and the [migration checklist](docs/migration.md). The vision describes the target;
the checklist distinguishes working capabilities from planned ones.

Start with [architecture](guides/architecture.md) when building an application.
Package READMEs document their current public APIs. Existing Streams integration
in Canon is retained; RPC integration is the next interoperability milestone.

The migration establishes a `uv` workspace with one root lockfile and separate
test processes for each member. See [contributing](docs/contributing.md) for
commands, [compatibility](docs/compatibility.md) for the tested scope, and
[releases](docs/releases.md) for the independent release policy.

The source repositories are preserved as Git ancestors, with exact imported
commits recorded in [the workspace decision](docs/design-decisions/0001-workspace.md).
This repository's current remote is `mathisarends/canon`; consolidating here does
not rename or archive the existing repositories.
