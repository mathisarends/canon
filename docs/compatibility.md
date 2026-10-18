# Compatibility

Published versions, verified on 2026-10-18:

| Distribution | Version | Import |
| --- | --- | --- |
| `fastapi-canon` | 0.5.1 | `fastapi_canon` |
| `fastapi-streams` | 0.2.0 | `fastapi_streams` |
| `fastapi-rpckit` (successor to pyrpckit 0.11.0) | 0.2.0 | `fastapi_rpckit` |

The root workspace supports Python `>=3.12,<3.15`, the intersection with Canon's
existing declared range. The combined stack needs FastAPI >=0.143.3 due to
Streams; Canon's independent requirement remains >=0.115,<1. All three versions
are available through PyPI and this repository's independent GitHub releases.

## Follow-up verification, 2026-10-18

The next source combination is Canon 0.5.2 / Streams 0.3.0 / RPCkit 0.2.0.
It is release preparation, not a publication or a verified external application
migration. Streams' request validation now runs at method call; see the
[upgrade notes](../packages/fastapi-streams/CHANGELOG.md#030---2026-10-18).
Local Windows validation passes lint/type gates, all package/root suites (1,453
Python tests in separate processes) and 22 TypeScript tests with generator drift
and coverage checks. Both six-combination wheel matrices pass with current
dependencies on Python 3.14 and direct minima on Python 3.12.12. Installed Streams
CLI checks pass core-only and with HTTPX/HTTPX2 installed separately. An additional
Python 3.12.12 wheel environment passes the generated SDK request/error/unknown
event smoke with FastAPI 0.143.3, Pydantic 2.11.2, Jinja 3.1.0, jsonschema 4.23.0
and HTTPX 0.28.0. Inventories are `dist/compatibility-latest.json` and
`dist/compatibility-minimum.json`; logs are `dist/sdk-hardening-*.log`.
Implementation `2d47c61` passed
[four-target CI](https://github.com/mathisarends/canon/actions/runs/39138900018),
the [Streams 0.3.0 dry run](https://github.com/mathisarends/canon/actions/runs/39139216592)
and the [Canon 0.5.2 dry run](https://github.com/mathisarends/canon/actions/runs/39139221925).
Downloaded wheel/sdist hashes match both exact-source manifests. Both workflows
passed current/minimum artifact and installed Streams backend gates; publication
and tag/GitHub Release jobs were skipped. These versions remain unreleased,
The user authorized publication on 2026-10-18. Changelogs are dated; final
dated-source CI and the publication/install/tag/GitHub Release gates are pending.

Canon 0.5.1, Streams 0.2.0 and RPCkit 0.2.0 are published. Final source
`4af9092` passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39127577804).
All three [publication workflows](releases.md#follow-up-publications-2026-10-18)
verified current/minimum wheel gates, public-index installs and matching GitHub
Releases. Downloaded PyPI, Actions and GitHub asset hashes, release notes and tags
match their exact-source manifests. Streams' public CLI/SDK passes core-only,
HTTPX and HTTPX2 separately. Public RPCkit passes both SDKs for Cara's 15-method
contract. An additional fresh Windows/Python 3.14 environment installs all three
exact versions together from PyPI and passes combined runtime/Dishka and generated
RPC client checks with FastAPI 0.144.0, Pydantic 2.14.1 and Dishka 1.10.1.
Full external application migration remains separate.

The initial checks below used RPCkit 0.1.1. That unpublished version is
superseded by 0.2.0 for the breaking signature/context changes; its old artifact
results do not validate the new version. Corrected source `0a2b097` separately
passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39126936002)
and the [RPCkit 0.2.0 dry run](https://github.com/mathisarends/canon/actions/runs/39127145156),
including current/minimum wheel and installed Streams backend gates. Downloaded
artifact hashes match its manifest. Runtime and generator behavior are unchanged
by the version fix; no publication had occurred at that preparation stage.

Local Windows checks passed 1,380 Python tests across isolated package/root
processes and 22 TypeScript tests, all lint/type gates, both generator drift
checks, and RPCkit's installed-wheel public type check (92.2%, minimum 92%).
The six independent wheel combinations pass with current compatible dependencies
on Python 3.14 and direct dependency minima on Python 3.12.12. Core-only imports
remain independent. The installed reference-service wheel also passes five tests.
Dependency inventories are `dist/compatibility-latest.json` and
`dist/compatibility-minimum.json`; these are local generated evidence, not a
claim of exhaustive transitive minima or public-index publication.

The minimum full-stack profile uses FastAPI 0.143.3, Pydantic 2.11.2,
Dishka 1.10.0, Jinja 3.1.0 and jsonschema 4.23.0. Canon alone also passes with
FastAPI 0.115.0 and Pydantic 2.9.0. An additional installed Streams CLI/client
smoke on Python 3.12 with FastAPI 0.143.3, Pydantic 2.11.2 and HTTPX 0.28.0
verifies preserved scalar constraints, strict unknown variants, opt-in skipping,
and malformed known-event rejection. Current-dependency installed CLI checks
also pass core-only and with HTTPX 0.28.1 or HTTPX2 2.13.1 installed separately.

The prepared source at `de05d8c` also passed
[four-target CI](https://github.com/mathisarends/canon/actions/runs/39126069250)
and all three [release dry runs](releases.md#verified-follow-up-preparation-2026-10-18).
Downloaded artifact hashes match their manifests; publication/tag jobs were skipped. Consumer
feedback from Maximus is reported evidence; full external application migrations
remain outside this verification. See the [feedback decision](design-decisions/0002-consumer-feedback.md).

There are two verification modes:

1. Workspace: one root lockfile, member-specific suites, current optional Streams
   integration, and a three-transport composition/lifecycle regression.
2. Artifacts: wheel/sdist builds; standalone wheel installs; Canon with Streams,
   RPC, and both; installed runtime and scope checks with no workspace overrides.

The artifact installer resolves third-party dependencies from published metadata.
It deliberately does not inherit the editable workspace. Direct dependency
minima and current compatible versions are checked below. This is a bounded smoke
matrix, not exhaustive coverage of every compatible dependency combination.
External application runtime migration remains open; Cara's exported RPC contract
is checked separately from running its service.

Root CI is configured to repeat workspace tests across Python 3.12–3.14 and
Windows 3.14, and artifact checks on Linux. Those configured targets are distinct
from the local results below.

## Initial consolidation verification, 2026-10-17

Windows x64, CPython 3.14.0, uv 0.9.2, Node.js 24:

- Shared dependency resolution: FastAPI 0.143.3, Starlette 1.8.0, Pydantic 2.14.1,
  Dishka 1.10.1. Exact development dependencies are in the root lockfile.
- Canon: 251 pytest cases; Streams: 232; RPC successor: 832; architecture reference
  service: 5 after its Canon migration; combined HTTP/SSE/RPC and Dishka scope
  regression: 1.
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
- The migrated architecture reference service is also built as a development
  artifact and installed with the Canon wheel in a seventh clean environment.
  Its five HTTP/authentication/Problem Details tests pass with both extensions
  absent and both application/library imports verified to come from site-packages.

The [initial consolidation CI run](https://github.com/mathisarends/canon/actions/runs/39030985598)
at commit `1adfe04` passed Linux/Python 3.12, 3.13, and 3.14 plus Windows/Python
3.14. The reference service in that initial run still used its original local
composition; the subsequent Canon migration adds the five canonical HTTP tests
and its own installed-artifact check without requiring either transport extension.

These are development verification results, not a published support promise.
External application migration and PyPI registration/publishing remain release
prerequisites. Existing fixture
warnings about optional SSE discriminators remain unchanged; artifact tests using
HTTPX can emit Starlette's upstream HTTPX2 migration warning.

## Release preparation verification, 2026-10-17

The prepared 0.5.0 / 0.1.0 / 0.1.0 packages pass fresh wheel installs and runtime
smoke checks in six combinations on Windows: each alone, Canon+Streams,
Canon+RPC, and all three. No workspace overrides are used in those environments.

| Combination | Minimum FastAPI | Minimum Pydantic | Minimum Dishka when used |
| --- | --- | --- | --- |
| Canon alone | 0.115.0 | 2.9.0 | 1.10.0 |
| Streams alone | 0.143.3 | 2.11.2 | — |
| RPC alone | 0.115.0 | 2.11.0 | — |
| Canon+Streams/codegen | 0.143.3 | 2.11.2 | 1.10.0 |
| Canon+RPC/codegen/Dishka | 0.115.0 | 2.11.0 | 1.10.0 |
| Full stack with codegen/Dishka/OTel | 0.143.3 | 2.11.2 | 1.10.0 |

Minimum mode runs on CPython 3.12.12. Requested codegen extras resolve Jinja2
3.1.0 and JSON Schema 4.23.0. In the full stack, FastAPI's transitive requirement
raises OTel API to 1.44.0 even though the RPC extra alone declares `>=1.30`.
The resolver chooses jointly satisfiable direct minima; it does not force every
transitive dependency to its oldest release.

Latest mode runs on CPython 3.14.0 with FastAPI 0.143.3, Pydantic 2.14.1,
Starlette 1.8.0, Dishka 1.10.1, Jinja2 3.1.6, JSON Schema 4.26.0 and OTel API
1.45.1 where applicable. The installed reference service passes its five tests
with Canon 0.5.0 and both extensions absent. Streams' core-only, HTTPX and HTTPX2
artifact/CLI checks also pass.

The workspace gates cover Canon's 251 tests, Streams' 232, RPC's 833 including
the new generator regression, the reference service's five and the composed
stack test. Client regeneration and drift checks include both RPC manifests.
The inherited optional-discriminator warnings remain documented. Local results
for this change do not imply a new CI result on every supported Python version.

[RPC parity and Cara contract evidence](rpc-parity.md) records the source audit,
consumer SDK compilation and the remaining full application migration. See the
[release guide](releases.md#prepare-a-version) for commands and generated
machine-readable dependency inventories.

## Release workflow verification, 2026-10-17

After the accepted rename to `fastapi-rpckit` / `fastapi_rpckit`, the
[CI run for `3d8c1de`](https://github.com/mathisarends/canon/actions/runs/39044259386)
passed on all four configured targets: Linux/Python 3.12, 3.13 and 3.14, and
Windows/Python 3.14. The Python suites now contain 1,348 tests, including 26
release-check regressions, and Streams retains its 22 TypeScript transport tests.
Client generation/drift checks cover the renamed RPC Python/TypeScript clients
and manifests. The renamed installed RPC wheel also passes both SDK checks for
Cara's exported 15-method contract; its full application migration remains open.

All three [GitHub release dry runs](releases.md#verified-dry-runs-2026-10-17)
passed the current-dependency and Python 3.12 direct-minimum artifact profiles,
plus installed Streams backend checks. Downloaded wheel/sdist hashes match their
reports. These runs checked preparation only; public-index results are recorded
below.

## Published-package verification, 2026-10-17

[Publication evidence](releases.md#first-publications-2026-10-17) links all three
successful release runs, source commits and GitHub releases. PyPI wheel/sdist
hashes match the original verified manifests and GitHub assets. Each release's
workflow passed fresh public-index installs; Canon passed both core-only and
`[streams]` installs.

Additional Windows/Python 3.14 checks installed all three pinned PyPI versions in
a fresh virtual environment without workspace overrides. HTTP, SSE, WebSocket
RPC, shared Dishka state and shutdown cleanup passed, along with an RPC generated
Python client roundtrip and strict TypeScript client compilation.

The downloaded public Streams wheel passed the core-only CLI diagnostic and
generated-client checks with HTTPX and HTTPX2 separately. Public RPC 0.1.0 passed
both SDK generation/drift/compilation checks for Cara's 15-method contract, with
Python package import and Ruff lint/format validation. These SDK checks do not
claim Cara's full application migration.
