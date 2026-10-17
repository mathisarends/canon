# Compatibility

Consolidation keeps Canon/Streams versions and creates a separately named RPC successor:

| Distribution | Version | Import |
| --- | --- | --- |
| `fastapi-canon` | 0.4.0 | `fastapi_canon` |
| `fastapi-streams` | 0.0.1 | `fastapi_streams` |
| `fastapi-wsrpc` (unreleased successor to pyrpckit 0.11.0) | 0.1.0 | `fastapi_wsrpc` |

The root workspace supports Python `>=3.12,<3.15`, the intersection with Canon's
existing declared range. The combined stack needs FastAPI >=0.143.3 due to
Streams; Canon's independent requirement remains >=0.115,<1. No package version
has been published from this repository.

There are two verification modes:

1. Workspace: one root lockfile, member-specific suites, current optional Streams
   integration, and a three-transport composition/lifecycle regression.
2. Artifacts: wheel/sdist builds; standalone wheel installs; Canon with Streams,
   RPC, and both; installed runtime and scope checks with no workspace overrides.

The artifact installer resolves third-party dependencies from published metadata.
It deliberately does not inherit the editable workspace. The first migration
checks current dependency resolution; a full released minimum/maximum support
matrix is still a release gate to implement, not a guarantee inferred from the
workspace lock. The shared stack has not yet been tested in external applications.

Root CI is configured to repeat workspace tests across Python 3.12–3.14 and
Windows 3.14, and artifact checks on Linux. Those configured targets are distinct
from the local results below.

## Local verification, 2026-10-17

Windows x64, CPython 3.14.0, uv 0.9.2, Node.js 24:

- Shared dependency resolution: FastAPI 0.143.3, Starlette 1.8.0, Pydantic 2.14.1,
  Dishka 1.10.1. Exact development dependencies are in the root lockfile.
- Canon: 251 pytest cases; Streams: 232; RPC successor: 832; architecture reference
  service: 2; combined HTTP/SSE/RPC and Dishka scope regression: 1.
- Ruff checks/formatting for every member; Canon/reference Mypy; Streams
  Pyright/Pylint; RPC public type completeness from an installed wheel (92.2%,
  existing threshold 92%).
- Both contract/client drift checks; Streams TypeScript typecheck and 22 transport
  tests with the existing coverage thresholds.
- Three wheel/sdist builds with strict Twine metadata checks and `py.typed`
  inspection. Wheels are also built back from their sdists.
- Six clean wheel-install cases: each library alone, Canon+Streams, Canon+RPC,
  and all three. Each passes `uv pip check`, installed-file/absent-module checks,
  and relevant HTTP/SSE/WebSocket runtime checks. The full stack also verifies
  shared Dishka state and shutdown cleanup.
- RPC Python/TypeScript clients generated from the installed server contract;
  Python client roundtrip and TypeScript compilation. Streams additionally runs
  its installed CLI/consumer checks in three environments: core-only, HTTPX,
  and HTTPX2.

These are development verification results, not a published support promise.
External application migration, all supported dependency minima/maxima, and
PyPI registration/publishing remain release prerequisites. Existing fixture
warnings about optional SSE discriminators remain unchanged; artifact tests using
HTTPX can emit Starlette's upstream HTTPX2 migration warning.
