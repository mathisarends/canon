# Canon

One workspace for the FastAPI application stack: architecture conventions,
feature composition and HTTP contracts, typed SSE, WebSocket RPC, and WebRTC
sessions.

The prepared Canon 0.9.0 source consolidates the stack into one `fastapi-canon`
distribution. Its modules include composition, HTTP contracts, SSE, WebSockets
and WebRTC. Extras select optional dependencies:

```console
uv add "fastapi-canon[sse,websockets,webrtc]"
uv add --dev "fastapi-canon[codegen]"
uv run canon --help
```

These changes are not published yet. See the
[migration guide](packages/fastapi-canon/docs/package-migration.md) for imports,
commands and the current codegen scope.

## Current releases

| Package | Version | GitHub | PyPI |
| --- | --- | --- | --- |
| `fastapi-canon` | 0.8.1 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.8.1) | [Install](https://pypi.org/project/fastapi-canon/0.8.1/) |
| `fastapi-streams` | 0.5.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.5.0) | [Install](https://pypi.org/project/fastapi-streams/0.5.0/) |
| `fastapi-rpckit` | 0.4.1 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-rpckit-v0.4.1) | [Install](https://pypi.org/project/fastapi-rpckit/0.4.1/) |
| `fastapi-webrtc` | 0.3.0 | [Release notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-webrtc-v0.3.0) | [Install](https://pypi.org/project/fastapi-webrtc/0.3.0/) |

Package releases appear in this repository's [central release list](https://github.com/mathisarends/canon/releases).
The table records verified publications. Future releases use one Canon version,
tag, changelog and artifact set; earlier package releases remain available.

## Workspace

| Component | Location | Distribution / import |
| --- | --- | --- |
| Composition, Dishka, HTTP contracts | [`packages/fastapi-canon`](packages/fastapi-canon) | `fastapi-canon` / `fastapi_canon` |
| Typed SSE and generated clients | [`SSE module`](packages/fastapi-canon/fastapi_canon/sse), [`tests and guides`](packages/fastapi-streams) | `fastapi-canon[sse]` / `fastapi_canon.sse` |
| WebSocket RPC and generated clients | [`WebSockets module`](packages/fastapi-canon/fastapi_canon/websockets), [`tests and guides`](packages/fastapi-rpckit) | `fastapi-canon[websockets]` / `fastapi_canon.websockets` |
| WebRTC sessions and generated browser clients | [`WebRTC module`](packages/fastapi-canon/fastapi_canon/webrtc), [`tests and guides`](packages/fastapi-webrtc) | `fastapi-canon[webrtc]` / `fastapi_canon.webrtc` |
| Architecture conventions | [`guides`](guides) | feature slices, inward dependencies, Dishka |
| Runnable architecture example | [`examples/reference-service`](examples/reference-service) | development-only workspace member |

`fastapi-rpckit` is the FastAPI-first successor to `pyrpckit`, with its existing
WebSocket engine and protocol retained. See the [RPC migration guide](packages/fastapi-rpckit/docs/migration.md).
Its initial release is 0.1.0. The existing source repositories remain available;
current development and future Canon releases live here.

Package READMEs and guides describe implemented APIs; [contributing](docs/contributing.md) covers development.

Start with [architecture](guides/architecture.md) when building an application.
Package READMEs document their current public APIs. Existing Streams integration
in Canon is retained; the [stack example](examples/stack_service.py) combines HTTP,
SSE, and RPC using the same Dishka application container.

Development uses a `uv` workspace with one root lockfile and separate
test processes for each member. See [contributing](docs/contributing.md) for
commands, [compatibility](docs/compatibility.md) for the tested scope, and
[releases](docs/releases.md) for publication checks and historical releases.

The imported repositories remain available in Git history. Current development
and releases use `mathisarends/canon`; predecessor repositories are preserved.
