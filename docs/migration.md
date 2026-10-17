# Consolidation checklist

## M0: reproduce the existing components

- [x] Inventory and fetch all four source `main` branches.
- [x] Preserve the vision and record package boundaries and source commits.
- [x] Import all package sources, tests, docs, and Git histories.
- [x] Replace package lockfiles with one uv workspace lockfile.
- [x] Coordinate package quality checks and tests from the root.
- [x] Build and exercise independently installed artifacts.
- [x] Verify reference-service tests and existing generated clients.

## M1: prove interoperability

- [x] Demonstrate HTTP, SSE, and WebSocket RPC in one composed FastAPI app.
- [x] Cover that composition using workspace members and built wheels.
- [x] Record tested versions without overstating minimum-version support.
- [x] Reuse the existing `dishka_router` in `Feature.routers`; the initial
      composition does not need a second RPC adapter.
- [ ] Adapt the architecture reference service to the current Canon library.

## M2 and M3: successor and releases

- [ ] Inventory consumer imports, RPC CLI, wire behavior, and client APIs.
- [x] Select `fastapi-wsrpc` / `fastapi_wsrpc` and check the PyPI JSON endpoint.
- [ ] Confirm registration acceptance and ownership before publication.
- [x] Make FastAPI required, expose its existing mounting APIs directly, and
      document the import/CLI migration. Further API redesign needs consumer tests.
- [ ] Test existing application consumers before removing public APIs.
- [ ] Define per-package tags, changelogs, compatibility gates, and protected
      PyPI Trusted Publishers for this repository.
- [ ] Release the successor, migrate consumers, then archive the predecessor.

The user requested the RPC successor rename during consolidation. Its new
distribution starts at unreleased 0.1.0; Canon and Streams preserve their source
versions and PyPI identities. No release, old-repository rename, deprecation,
or archival has been performed.
