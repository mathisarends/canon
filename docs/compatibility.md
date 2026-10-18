# Compatibility

Published versions, verified on 2026-10-18:

| Distribution | Version | Import |
| --- | --- | --- |
| `fastapi-canon` | 0.5.3 | `fastapi_canon` |
| `fastapi-streams` | 0.3.1 | `fastapi_streams` |
| `fastapi-rpckit` (successor to pyrpckit 0.11.0) | 0.2.0 | `fastapi_rpckit` |

The root workspace supports Python `>=3.12,<3.15`, the intersection with Canon's
existing declared range. The combined stack needs FastAPI >=0.143.3 due to
Streams; Canon's independent requirement remains >=0.115,<1. All three versions
are available through PyPI and this repository's independent GitHub releases.

## Follow-up verification, 2026-10-18

### SDK review release preparation

Prepared source versions are Canon 0.5.4 / Streams 0.4.0 / RPCkit 0.2.0; the
published versions above remain current until separate publication approval.
Streams uses the next minor version because manifest provenance makes drift
checks stricter. Existing SDK callers and HTTP/SSE contracts stay compatible.

The complete root workspace gate passes 1,463 Python tests and 23 TypeScript
tests, lint, package-specific type checks, generator drift and coverage checks.
The generated TypeScript transport has 100% line coverage, 93.44% branch coverage
and 95.24% function coverage. The local log is
`dist/consumer-review-workspace.log`.

Local Windows verification passes both six-combination installed-wheel matrices:
current compatible dependencies on Python 3.14 and minimum direct dependencies
on Python 3.12. The current matrix also passes the independently installed
reference service's five tests. Inventories are `dist/compatibility-latest.json`
and `dist/compatibility-minimum.json`.

Fresh installed Streams environments pass core-only CLI diagnostics and
generation/drift/runtime/TypeScript checks with HTTPX and HTTPX2 separately.
These include manifest/report provenance equality for each target/backend.
Logs are `dist/consumer-review-distributions-current.log`,
`dist/consumer-review-distributions-minimum.log` and
`dist/consumer-review-streams-artifacts.log`. Consumer-reported Maximus adoption
and remaining Hermes/browser coverage are recorded separately in TODO.md.

### SDK efficiency publications

The current public combination is Canon 0.5.3 / Streams 0.3.1 / RPCkit 0.2.0.
Final source `c9041d4` passed
[Linux/Python 3.12–3.14 and Windows/Python 3.14 CI](https://github.com/mathisarends/canon/actions/runs/39145291158).
Both release dry runs passed on that source: [Streams](https://github.com/mathisarends/canon/actions/runs/39145653393)
and [Canon](https://github.com/mathisarends/canon/actions/runs/39145658246).
The authorized [Streams publication](https://github.com/mathisarends/canon/actions/runs/39145824967)
completed and was independently verified before the
[Canon publication](https://github.com/mathisarends/canon/actions/runs/39146194609).
Both workflows passed current/minimum wheel and installed Streams backend gates,
public PyPI checks, fresh public installs and matching GitHub Releases. Canon
covered core-only and `[streams]`. PyPI, Actions and GitHub asset hashes match
the original manifests and dry runs; package-prefixed tags, notes and attached
artifacts were independently checked. See the [release evidence](releases.md#sdk-efficiency-publications-2026-10-18).

An additional fresh Windows/Python 3.14 public-index environment passes Streams'
HTTPX2 generated SDK/CLI smoke, including early request rejection, event
validation, structured errors, unknown-event policy, report provenance/capabilities
and TypeScript compilation. A separate public-index environment installs all
three exact versions together and passes combined HTTP/SSE/RPC, shared Dishka
state/cleanup and generated RPC clients. Inventories are
`dist/publications/public-streams-httpx2-0.3.1-inventory.json` and
`dist/publications/public-stack-sdk-efficiency-inventory.json`.

Initial index visibility delays were resolved by retrying the same public
versions; Streams resumed only failed jobs on its original run, without another
upload. Downloaded evidence is under `dist/publications/39145824967/` and
`dist/publications/39146194609/`; logs are `dist/sdk-efficiency-publication-*.log`,
`dist/sdk-efficiency-*-verification.log` and `dist/sdk-efficiency-public-*.log`.
These results verify the published stack, not full external application or
native Hermes deployment coverage.

### SDK efficiency patch preparation

Preparation used Canon 0.5.3 / Streams 0.3.1 / RPCkit 0.2.0 before publication;
the subsequent public verification is recorded above. RPCkit is unchanged.
The [release record](releases.md#sdk-efficiency-publications-2026-10-18)
and [validation/performance decision](design-decisions/0004-sdk-validation-efficiency.md)
record scope, upgrade steps and bounded benchmark results.

Local Windows/Python 3.14 checks pass all workspace gates: lint/formatting, package
type checks, 1,458 Python tests in separate processes (Canon 251, Streams 320,
RPCkit 839, reference service 5 and root integration/release 43), generator drift
and 22 TypeScript tests with transport coverage. The initial combined check
exposed seven root release tests still tied to the previous version numbers;
after updating those fixtures, the complete root suite and remaining client gate
pass separately. Existing unsupported-constraint and upstream deprecation warnings
remain expected. No application runtime validation failure was found.

Both independent six-combination wheel matrices pass: current compatible
dependencies on Python 3.14 and direct minima on Python 3.12.12. The current
profile also installs the reference-service wheel and passes its five tests with
both extensions absent. Installed Streams checks pass core-only, HTTPX-only and
HTTPX2-only environments, including generated diagnostic provenance/capabilities,
request/event failures and unknown-event policy. An additional fresh Python
3.12.12 wheel environment passes that SDK/CLI smoke with FastAPI 0.143.3,
Pydantic 2.11.2, HTTPX 0.28.0, Jinja 3.1.0 and jsonschema 4.23.0.

Dependency inventories are `dist/compatibility-latest.json` and
`dist/compatibility-minimum.json`. Logs are `dist/sdk-efficiency-checks.log`,
`dist/sdk-efficiency-root-tests.log`, `dist/sdk-efficiency-clients.log`,
`dist/sdk-efficiency-artifacts-current.log`, `dist/sdk-efficiency-artifacts-minimum.log`,
`dist/sdk-efficiency-streams-artifacts.log` and `dist/sdk-efficiency-minimum-sdk.log`.
These are local source/artifact results, not exact-commit CI, release dry runs,
public-index publication verification or native Hermes/application coverage.

### SDK hardening publications

The SDK hardening publication verified Canon 0.5.2 / Streams 0.3.0 / RPCkit 0.2.0.
This verifies the published stack; full external application migration remains
separate. Streams' request validation now runs at method call; see the
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
and tag/GitHub Release jobs were skipped at the preparation stage.

The final dated source `782d990` passed
[four-target CI](https://github.com/mathisarends/canon/actions/runs/39140129032).
The authorized [Streams 0.3.0 publication](https://github.com/mathisarends/canon/actions/runs/39140501009)
completed before [Canon 0.5.2](https://github.com/mathisarends/canon/actions/runs/39140884839).
Both workflows verified current/minimum wheels, installed Streams CLI/backends,
public-index installs and matching GitHub Releases. Canon passed core-only and
`[streams]` installs. Independently downloaded PyPI, Actions and GitHub assets
match their exact-source manifests; tags, dated changelog notes and attached
files were verified. A fresh Windows/Python 3.14 public-index environment also
passes the installed Streams CLI and HTTPX2 generated SDK smoke, including
request/body constraints, structured stream errors and known/unknown event policy.
TypeScript output compiles. A second fresh public-index environment verifies
Canon 0.5.2, Streams 0.3.0 and RPCkit 0.2.0 together, including combined HTTP/SSE/RPC,
Dishka state/cleanup and generated RPC clients. Its dependency inventory is
`dist/publications/public-stack-sdk-hardening-inventory.json`. Evidence is under
`dist/publications/`; initial local index-visibility delays were resolved by
refreshing metadata and retrying the same public versions without another upload.

### Previous consumer-feedback publications

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
