# Consolidation checklist

## M0: reproduce the existing components

- [x] Inventory and fetch all four source `main` branches.
- [x] Preserve the vision and record package boundaries and source commits.
- [ ] Import all package sources, tests, docs, and Git histories.
- [ ] Replace package lockfiles with one uv workspace lockfile.
- [ ] Coordinate package quality checks and tests from the root.
- [ ] Build and exercise independently installed artifacts.
- [ ] Verify reference-service tests and existing generated clients.

## M1: prove interoperability

- [ ] Demonstrate HTTP, SSE, and WebSocket RPC in one composed FastAPI app.
- [ ] Cover that composition using workspace members and built wheels.
- [ ] Record tested versions without overstating minimum-version support.
- [ ] Decide whether an RPC composition adapter is needed from the example.
- [ ] Adapt the architecture reference service to the current Canon library.

## M2 and M3: successor and releases

- [ ] Inventory consumer imports, RPC CLI, wire behavior, and client APIs.
- [ ] Verify and select a distinct RPC distribution name and import path.
- [ ] Define the FastAPI-first public API and document migration.
- [ ] Test existing application consumers before removing public APIs.
- [ ] Define per-package tags, changelogs, compatibility gates, and protected
      PyPI Trusted Publishers for this repository.
- [ ] Release the successor, migrate consumers, then archive the predecessor.

No release, repository rename, deprecation, or archival is part of the initial
workspace import. Versions are preserved from the imported source metadata.
