# Canon

One workspace for the FastAPI application stack: architecture conventions,
feature composition and HTTP contracts, typed SSE, WebSocket RPC, and WebRTC
sessions.

Canon is the ecosystem; `fastapi-canon` is its application-composition package.
The libraries remain independently installable and independently versioned.

## Current releases

| Package | Version | GitHub | PyPI |
| --- | --- | --- | --- |
| `fastapi-canon` | 0.6.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.6.0) | [Install](https://pypi.org/project/fastapi-canon/0.6.0/) |
| `fastapi-streams` | 0.4.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.4.0) | [Install](https://pypi.org/project/fastapi-streams/0.4.0/) |
| `fastapi-rpckit` | 0.4.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-rpckit-v0.4.0) | [Install](https://pypi.org/project/fastapi-rpckit/0.4.0/) |
| `fastapi-webrtc` | 0.2.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-webrtc-v0.2.0) | [Install](https://pypi.org/project/fastapi-webrtc/0.2.0/) |

Package releases appear in this repository's [central release list](https://github.com/mathisarends/canon/releases).
Each has its own version, package-prefixed tag, changelog and distribution files.

## Workspace

| Component | Location | Distribution / import |
| --- | --- | --- |
| Composition, Dishka, HTTP contracts | [`packages/fastapi-canon`](packages/fastapi-canon) | `fastapi-canon` / `fastapi_canon` |
| Typed SSE and generated clients | [`packages/fastapi-streams`](packages/fastapi-streams) | `fastapi-streams` / `fastapi_streams` |
| WebSocket RPC and generated clients | [`packages/fastapi-rpckit`](packages/fastapi-rpckit) | `fastapi-rpckit` / `fastapi_rpckit` |
| WebRTC sessions and generated browser clients | [`packages/fastapi-webrtc`](packages/fastapi-webrtc) | `fastapi-webrtc` / `fastapi_webrtc` |
| Architecture conventions | [`guides`](guides) | feature slices, inward dependencies, Dishka |
| Runnable architecture example | [`examples/reference-service`](examples/reference-service) | development-only workspace member |

`fastapi-rpckit` is the FastAPI-first successor to `pyrpckit`, with its existing
WebSocket engine and protocol retained. See the [RPC migration guide](packages/fastapi-rpckit/docs/migration.md).
Its initial release is 0.1.0. The existing source repositories remain available;
current development and releases for all four packages live here.

[TODO.md](TODO.md) lists prioritized open work. Package READMEs and guides
describe implemented APIs; [contributing](docs/contributing.md) covers development.

Start with [architecture](guides/architecture.md) when building an application.
Package READMEs document their current public APIs. Existing Streams integration
in Canon is retained; the [stack example](examples/stack_service.py) combines HTTP,
SSE, and RPC using the same Dishka application container.

Development uses a `uv` workspace with one root lockfile and separate
test processes for each member. See [contributing](docs/contributing.md) for
commands, [compatibility](docs/compatibility.md) for the tested scope, and
[releases](docs/releases.md) for the independent release policy.

The imported repositories remain available in Git history. Current development
and releases use `mathisarends/canon`; predecessor repositories are preserved.
