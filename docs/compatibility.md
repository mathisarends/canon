# Compatibility

Consolidation preserves these source versions:

| Distribution | Version | Import |
| --- | --- | --- |
| `fastapi-canon` | 0.4.0 | `fastapi_canon` |
| `fastapi-streams` | 0.0.1 | `fastapi_streams` |
| `pyrpckit` (before successor rename) | 0.11.0 | `rpckit` |

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

Root CI repeats workspace tests across Python 3.12–3.14 and Windows 3.14, and
artifact checks on Linux. Local results and remaining limitations are recorded
below after migration verification.
