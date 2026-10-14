# Documentation

Read the [hardening stack and SDK migration guide](hardening-overview.md) for all
15 ticket PRs, changed defaults, and integration steps.

The README explains why rpckit exists and gets a first service running. These
guides cover the individual parts of the API in more detail:

- [Services and channels](services.md) — define methods and assemble endpoints
- [JSON-RPC protocol](protocol.md) — request cancellation and wire conventions
- [Dependency injection](dependencies.md) — pass application services into handlers
- [Connections and events](connections-and-events.md) — inspect connections and push updates
- [Client methods](client-methods.md) — let the server call the connected client
- [Typed errors](errors.md) — make expected failures part of the contract
- [Binary streams](streams.md) — stream bytes on dedicated endpoints
- [Raw sockets](raw-sockets.md) — proxy native WebSocket protocols with text and binary messages
- [Observability](observability.md) — instrument calls and streams with middleware and OpenTelemetry
- [Contract and clients](clients.md) — export OpenRPC and generate typed clients
- [Transports](transports.md) — serve with FastAPI, a custom adapter, or in-memory tests
- [Releasing](releasing.md) — version, validate, and tag a release

Start with services and channels if you are building a server. Start with the
contract and client guide if the server definition already exists.

The stable import surface is `rpckit` plus the documented integration
modules `rpckit.integrations.fastapi`, `rpckit.integrations.dishka`, and
`rpckit.integrations.opentelemetry`, plus `rpckit.testing` and `rpckit.codegen`.
Other submodules are implementation details.
