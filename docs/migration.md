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
- [x] Adapt the architecture reference service to the current Canon library,
      including canonical HTTP error contracts and matching agent guides.

## M2 and M3: successor and releases

- [x] Inventory consumer imports, RPC CLI, wire behavior, and client APIs;
      see [RPC parity and Cara contract checks](rpc-parity.md).
- [x] Select `fastapi-rpckit` / `fastapi_rpckit` and check the PyPI JSON endpoint.
- [x] Confirm Pending Publisher acceptance for `fastapi-rpckit` after PyPI rejected
      the initially selected `fastapi-wsrpc` name for similarity. The first OIDC
      upload created the project on 2026-10-17.
- [x] Make FastAPI required, expose its existing mounting APIs directly, and
      document the import/CLI migration. Further API redesign needs consumer tests.
- [ ] Test existing application consumers before removing public APIs.
- [x] Define per-package tags, changelogs, compatibility gates, and protected
      PyPI Trusted Publishers for this repository.
- [x] Publish all three packages with separate tags and GitHub releases; verify
      PyPI files, fresh installs and generated SDKs.
- [x] Add `fastapi-webrtc` as an independent extension (issue #2); see
      [decision 0005](design-decisions/0005-webrtc-extension.md). Unreleased.
- [ ] Complete external application migrations. Archive the predecessor only
      after a separate explicit decision.

The user requested the RPC successor rename during consolidation. Its new
distribution starts at 0.1.0; Canon and Streams preserve their PyPI identities and
have released 0.5.0 and 0.1.0 respectively. All current releases are listed in the
[README](../README.md#current-releases) and this repository's GitHub Releases.
No old-repository rename, deprecation or archival has been performed.
