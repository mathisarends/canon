# Independent releases

Release one library at a time from `mathisarends/canon`. All three libraries have
published releases from this repository. The root workspace and reference service
are not publication targets. The [README](../README.md#current-releases) lists all
current package versions with PyPI and GitHub release links.

## SDK review publications

The user explicitly authorized publication in this chat after preparation,
exact-source CI and both dry runs. **Streams 0.4.0** and **Canon 0.5.4** are
published and independently verified; RPCkit stays 0.2.0. Streams was published
on 2026-10-18 and verified before Canon's dispatch on 2026-10-19. Verification
of both publications completed on 2026-10-19.

Both releases use the approved, dated source
[`81f71c4`](https://github.com/mathisarends/canon/commit/81f71c4ffca14d4de5ea3e69c5523e092ea86eec),
which passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39150170862)
and the [Streams dry run](https://github.com/mathisarends/canon/actions/runs/39150549837)
and [Canon dry run](https://github.com/mathisarends/canon/actions/runs/39150582335).
The changelog dates were finalized in that source on 2026-10-18; the source and
tags were not changed when Canon's publication completed the following day.

| Package | Version | Publication workflow | GitHub Release |
| --- | --- | --- | --- |
| Streams | [0.4.0](https://pypi.org/project/fastapi-streams/0.4.0/) | [39151048114](https://github.com/mathisarends/canon/actions/runs/39151048114) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.4.0) |
| Canon | [0.5.4](https://pypi.org/project/fastapi-canon/0.5.4/) | [39208726015](https://github.com/mathisarends/canon/actions/runs/39208726015) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.5.4) |

Streams records generator/version, canonical source-schema hash, target and HTTP
backend in each CLI-generated SDK manifest. It is a minor release because drift
checks now reject older files-only manifests and changed provenance, including
schema changes that leave generated source identical. Regenerate once with the
existing language/backend and commit the manifest. Diagnostic IDs/allowances,
runtime signatures, HTTP/SSE contracts and valid caller behavior are unchanged.
Consumer decoder recipes reuse the existing optional TypeScript guard and cached
Python adapters, retaining generic unexpected-response handling.

Canon only updates the optional/development Streams pin; it is an independent
patch with unchanged composition APIs. The shared release CLI now resolves
inline changelog links to the verified release commit. The existing Canon 0.5.3 release body was corrected to
link to its original `c9041d4` source; its tag and asset metadata are unchanged.

Both publication workflows passed current/minimum wheel matrices and installed
Streams CLI/backend checks on their actual upload artifacts. They then verified
PyPI hashes and fresh public-index installs; Canon covered core-only and
`[streams]`. Both workflows completed on their first attempt.

Independent downloads confirm byte-identical wheel/sdist files across the dry
runs, publication Actions artifacts, GitHub assets and PyPI. Each public stable
GitHub Release has exactly the original wheel, sdist and manifest attached;
its manifest is byte-identical to the Actions original. Both tags resolve to
`81f71c4`, and notes match the rendered changelog with commit-pinned links.
Verified receipts and downloads are under `dist/publications/39151048114/` and
`dist/publications/39208726015/`; dry-run evidence is under `dist/dry-runs/`.

Additional fresh Windows/Python 3.14 public-index environments pass the Streams
HTTPX2 CLI/generated-SDK smoke, including manifest/report provenance equality,
and all three exact public versions together, including combined HTTP/SSE/RPC,
Dishka state/cleanup and generated RPC clients. Inventories are
`dist/publications/public-sdk-review-streams-inventory.json` and
`dist/publications/public-sdk-review-stack-inventory.json`. An initial local
Streams install could not yet resolve 0.4.0; retrying the explicit public index
with refreshed metadata succeeded. No published files or tags were replaced.

Local preparation also passed 1,463 Python tests, 23 TypeScript tests, lint/types,
generator drift/coverage and both six-combination wheel matrices. See
[compatibility evidence](compatibility.md#sdk-review-publications-verified-2026-10-19).
Logs are `dist/consumer-review-workspace.log`,
`dist/consumer-review-*-publication.log`, `dist/consumer-review-*-verification.log`
and `dist/consumer-review-public-*.log`. Full external application migration
remains separate.

## Current released versions

Published and verified: **Streams 0.4.0** (SDK manifest provenance and optional
consumer decoder recipes) and **Canon 0.5.4** (optional Streams pin).
RPCkit stays 0.2.0. Streams was published and verified first; the user explicitly
authorized both publications, including GitHub Releases and original artifacts.

| Distribution | Import | Version | Tag |
| --- | --- | --- | --- |
| `fastapi-streams` | `fastapi_streams` | 0.4.0 | `fastapi-streams-v0.4.0` |
| `fastapi-canon` | `fastapi_canon` | 0.5.4 | `fastapi-canon-v0.5.4` |
| `fastapi-rpckit` | `fastapi_rpckit` | 0.2.0 | `fastapi-rpckit-v0.2.0` |

Published Canon 0.5.4 pins Streams 0.4.0 in its `streams` extra. These releases
replace Canon 0.5.3 and Streams 0.3.1; RPC is independent. Regenerate SDKs once
with the existing language/backend and commit `.fastapi-streams.json` before
checking drift. Existing callers and reviewed diagnostic allowances are unchanged.
Versions do not need to match; changed builds require new versions.

`release.toml` maps distributions, directories, modules and tag prefixes. Versions
come from package metadata; the release check does not import business modules.

## Release-note links

The release CLI renders relative inline Markdown links from the selected
changelog section as absolute GitHub links to the verified release commit.
Paths resolve relative to the package's changelog, retaining anchors and link
titles. For example, Canon's `../fastapi-streams/CHANGELOG.md` points to
`packages/fastapi-streams/CHANGELOG.md` at that commit. Absolute external links
remain unchanged. Repository changelogs retain their relative links.

Generated `release-notes.md` is used for both dry-run review and GitHub Release
creation. Existing published notes are not changed by local regeneration;
correcting an older release body is a separate repository update, without
rebuilding artifacts or moving tags.

## SDK efficiency publications, 2026-10-18

Published and independently verified:

| Distribution | Version | Scope |
| --- | --- | --- |
| Streams | 0.3.1 | Cache ignore-policy metadata/JSON adapters, avoid unused error details, add provenance/validation-phase reports and benchmarks. |
| Canon | 0.5.3 | Optional/development Streams 0.3.1 pin; composition API unchanged. |
| RPCkit | 0.2.0 | Unchanged; no new publication. |

These are patches because public signatures, accepted inputs, defaults and wire
contracts remain unchanged. Report additions retain version 1 and existing
diagnostic IDs/allowances. Regenerate Python SDKs using the existing backend to
obtain the runtime improvement; existing generated SDKs remain compatible.
TypeScript stays static-only. See the [decision and benchmark evidence](design-decisions/0004-sdk-validation-efficiency.md)
and each package changelog for upgrade steps.

The user explicitly authorized both publications with matching GitHub Releases
on 2026-10-18. Final dated source
[`c9041d4`](https://github.com/mathisarends/canon/commit/c9041d43d0bc7ca3e270070d4a2b0e025bbd6815)
passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39145291158)
and both release dry runs: [Streams](https://github.com/mathisarends/canon/actions/runs/39145653393)
and [Canon](https://github.com/mathisarends/canon/actions/runs/39145658246).
Both dry runs passed current/minimum wheel matrices and installed Streams
CLI/backends; downloaded wheels/sdists match their exact-source manifests.

| Package | Version | Publication workflow | GitHub Release |
| --- | --- | --- | --- |
| Streams | [0.3.1](https://pypi.org/project/fastapi-streams/0.3.1/) | [39145824967](https://github.com/mathisarends/canon/actions/runs/39145824967) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.3.1) |
| Canon | [0.5.3](https://pypi.org/project/fastapi-canon/0.5.3/) | [39146194609](https://github.com/mathisarends/canon/actions/runs/39146194609) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.5.3) |

Streams completed publication and independent verification before Canon's
dispatch. Both tags resolve to `c9041d4`. Public PyPI downloads, Actions artifacts
and GitHub Release assets have identical wheel/sdist SHA-256 values, matching
both the original publication manifests and dry-run artifacts. Each public,
stable GitHub Release has its dated changelog notes and exactly the original
wheel, sdist and manifest attached. Notes match the repository changelogs;
attached manifests are byte-identical to the Actions originals.

Both workflows verified fresh public-index installs; Canon covered core-only
and `[streams]`. An additional Windows/Python 3.14 public-index environment
passes Streams' HTTPX2 CLI/generated SDK smoke, including request/event failures,
unknown-event policy, report provenance/capabilities and TypeScript compilation.
A second fresh public-index environment passes all three exact published
versions together, including combined HTTP/SSE/RPC, Dishka state/cleanup and
generated RPC clients. Its inventory is
`dist/publications/public-stack-sdk-efficiency-inventory.json`.

Streams' first post-upload public install encountered temporary index visibility
lag. Rerunning only failed jobs on the original run verified the same existing
files, skipped another upload and completed the GitHub Release. Canon completed
on its first workflow attempt. Local public-index checks also required metadata
refresh/retry for the same versions. No published contents were replaced and no
existing tags were moved. Downloaded evidence is under `dist/publications/39145824967/`
and `dist/publications/39146194609/`; dry-run evidence is under `dist/dry-runs/`.
Logs are `dist/sdk-efficiency-publication-*.log`,
`dist/sdk-efficiency-*-verification.log` and `dist/sdk-efficiency-public-*.log`.
Full external application migration remains separate.

Local validation passes 1,458 Python tests, 22 TypeScript tests, lint/types,
generator drift and coverage, both six-combination current/minimum wheel matrices,
isolated Streams CLI/backends and a minimum-dependency Python 3.12 SDK smoke.
The README's current-release table now records these verified public versions.

## SDK hardening publications, 2026-10-18

The final dated source [`782d990`](https://github.com/mathisarends/canon/commit/782d990163b2b8172218d12306dd596e5e6b6835)
passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39140129032).
The user explicitly authorized publication and matching GitHub Releases.

| Package | Published version | Successful publication | GitHub Release |
| --- | --- | --- | --- |
| Streams | [0.3.0](https://pypi.org/project/fastapi-streams/0.3.0/) | [39140501009](https://github.com/mathisarends/canon/actions/runs/39140501009) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.3.0) |
| Canon | [0.5.2](https://pypi.org/project/fastapi-canon/0.5.2/) | [39140884839](https://github.com/mathisarends/canon/actions/runs/39140884839) | [Notes and assets](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.5.2) |

Streams completed publication and verification before Canon's dispatch. Both
package-prefixed tags point to `782d990`. Each workflow passed current/minimum
artifact gates, isolated Streams CLI/backends, public PyPI hashes and fresh public
installs. Canon passed both core-only and `[streams]` public installs.

Independent downloads verify identical wheel/sdist SHA-256 values across PyPI,
Actions and GitHub Release assets, matching original manifests and exact-source
CI. Each GitHub Release has the dated changelog notes, original wheel, sdist and
manifest; release bodies match both workflow notes and repository changelogs.
An additional fresh Windows/Python 3.14 public-index environment passes Streams'
installed CLI, Python HTTPX2 SDK and TypeScript compilation. A second fresh public
environment installs Canon 0.5.2, Streams 0.3.0 and RPCkit 0.2.0 together and passes
combined HTTP/SSE/RPC, Dishka cleanup and generated RPC client checks. Initial
local index-visibility delays were resolved with refreshed metadata and retries;
no second upload or artifact replacement was needed.
Evidence and inventories are under `dist/publications/`; command logs are
`dist/sdk-publication-*.log`. Full external application migration remains separate.

## SDK hardening preparation, 2026-10-18

Implementation commit [`2d47c61`](https://github.com/mathisarends/canon/commit/2d47c61fbfa941b01795b40b9f177c4edd822407)
passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39138900018)
(Linux/Python 3.12, 3.13 and 3.14; Windows/Python 3.14). Local checks also passed
1,453 Python tests, 22 TypeScript tests, lint/types, generator drift/coverage,
current/minimum wheel matrices, isolated Streams CLI/backends, and an installed
Python 3.12 SDK smoke with the minimum Pydantic/FastAPI/codegen dependencies.

| Prepared package | Version | Successful dry run |
| --- | --- | --- |
| Streams | 0.3.0 | [39139216592](https://github.com/mathisarends/canon/actions/runs/39139216592) |
| Canon | 0.5.2 | [39139221925](https://github.com/mathisarends/canon/actions/runs/39139221925) |

Both manifests identify that exact implementation commit and successful CI.
Downloaded wheel and sdist SHA-256 values match every manifest. Both dry runs
passed current/minimum dependency artifact gates and isolated installed Streams
CLI/backend checks. PyPI publication and tag/GitHub Release jobs were skipped.
Original evidence is under `dist/dry-runs/RUN_ID/` and in the workflow artifacts.

This preparation does not publish either version or establish a full external
application migration. The following documentation commit records the evidence;
package sources and changelogs were unchanged and unreleased at that stage.
The user subsequently authorized publication on 2026-10-18. The final dated source
passed CI, and Streams and Canon publications were verified as recorded above.

## Follow-up releases, 2026-10-18

| Package | Released version | Scope |
| --- | --- | --- |
| Streams | 0.2.0 | Scalar validation preservation, unsupported-rule diagnostics, opt-in unknown-event ignoring, native/mixed-codegen recipes. |
| Canon | 0.5.1 | Streams 0.2.0 optional/development pin and corrected integration guidance. |
| RPCkit | 0.2.0 | Breaking Dishka signature/context clarification, authenticated example and canonical FastAPI documentation. |

These versions are published and independently verified. Streams' regenerated Python SDKs may reject
payloads that previously passed because constraints were dropped; read its
changelog before regeneration. Publish Streams before Canon. RPCkit keeps wire
contracts, `RpcRoutes` and existing nested imports. The user explicitly authorized
publication on 2026-10-18; changelogs are dated for that release. Public-index
installs and matching GitHub Releases are verified. Preparation and publication
evidence are recorded below.

RPCkit's originally prepared 0.1.1 was superseded by 0.2.0 after classifying the
mounting signature and context validation as breaking. Its earlier dry-run entry
below remains historical; the corrected 0.2.0 evidence is recorded below.

## Verified follow-up preparation, 2026-10-18

Prepared source commit [`de05d8c`](https://github.com/mathisarends/canon/commit/de05d8c272c297192c9e8e69d6738387038217b2)
passed [all four CI targets](https://github.com/mathisarends/canon/actions/runs/39126069250)
(Linux/Python 3.12, 3.13 and 3.14; Windows/Python 3.14).

| Package | Unpublished version | Successful dry run |
| --- | --- | --- |
| Streams | 0.2.0 | [39126396251](https://github.com/mathisarends/canon/actions/runs/39126396251) |
| Canon | 0.5.1 | [39126398149](https://github.com/mathisarends/canon/actions/runs/39126398149) |
| RPCkit | 0.1.1 | [39126399949](https://github.com/mathisarends/canon/actions/runs/39126399949) |

All three manifests record that exact commit, successful CI and artifact gates.
The downloaded wheel and sdist SHA-256 values match every manifest. Each dry run
passed current/minimum installed-wheel combinations and installed Streams backend
checks. Publishing and tag/release jobs were skipped. No packages, tags or GitHub
releases were published by this preparation. Local evidence is under
`dist/dry-runs/RUN_ID/`; workflow artifacts retain the original checked bytes.

The following documentation commit records this evidence; it does not change
runtime or generator behavior. Before an authorized publication, finalize changelog
dates, pass CI on the final source and follow the normal dry-run/publication flow.
The current-release table continues to describe only published versions.

### RPCkit version correction verified

The user requires every pre-1.0 breaking change to use the next minor version
with patch zero. Commit [`0a2b097`](https://github.com/mathisarends/canon/commit/0a2b097b2842ed7f95753047f16bc35a5cce4969)
corrects RPCkit to 0.2.0, records the rule in agent guidance, and enforces declared
breaking changelog sections during release validation. All 42 release tests pass.

That exact commit passed [four-target CI](https://github.com/mathisarends/canon/actions/runs/39126936002)
and the [RPCkit 0.2.0 dry run](https://github.com/mathisarends/canon/actions/runs/39127145156).
The downloaded wheel/sdist hashes match its manifest. Current/minimum wheel gates
and installed Streams backends passed; publication and tag/release jobs were
skipped. The earlier RPCkit 0.1.1 result above is superseded preparation evidence,
not a publication or verification of 0.2.0. At that preparation stage, sources
remained unreleased.

## Account configuration verified on 2026-10-17

| PyPI project | Publisher state |
| --- | --- |
| `fastapi-canon` | Trusted Publisher configured and verified |
| `fastapi-streams` | Trusted Publisher configured and verified |
| `fastapi-rpckit` | Initial Pending Publisher accepted; first OIDC publication verified |

All use GitHub owner `mathisarends`, repository `canon`, workflow filename
`release.yml`, and environment `pypi`. No persistent PyPI token is needed. The
GitHub environment allows only `main`. No additional reviewer or wait timer is
configured: publication uses manual dispatch and the gates below. Agents still
need explicit user authorization to dispatch a real publication.

PyPI rejected the initial `fastapi-wsrpc` name as too similar to an existing
project. The user selected `fastapi-rpckit` / `fastapi_rpckit`, and PyPI accepted
its pending publisher. The first successful OIDC upload created the project on
2026-10-17. Pending registration alone did not reserve the name. See
[PyPI's pending publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Prepare a version

### Version policy before 1.0

Every breaking change advances `0.x.y` to `0.(x+1).0`. Patch releases contain
only backward-compatible fixes and documentation. This includes changes to public
signatures, accepted inputs, validation, defaults and generated-client contracts;
an unchanged wire format does not make a source API change compatible. Classify
the impact before choosing a version and keep package versions independent.

Use a `### Breaking changes` heading (or `### Breaking generated-code changes`)
and document concrete migration steps. Release validation rejects a declared
pre-1.0 breaking release unless it has the next minor version and patch zero. A small
implementation change is not a reason to choose a patch release.

1. Review changes and update the package's `pyproject.toml`, changelog and existing
   `__version__` constant. Canon obtains its version from installed metadata.
2. Update root pins, Canon's Streams optional/development pins and the reference
   service's Canon range when needed. Run `uv lock`, retaining one root lockfile.
3. Regenerate clients through their generators and run the local gates below.
4. Commit/open a PR and merge to `main`, or commit directly when authorized.
   Wait for the complete `ci.yml` run on that exact commit to pass.
5. Run the selected package's dry run. Before publication, finalize its heading as
   `## VERSION - YYYY-MM-DD`, commit/push and wait for that exact CI run too.
   Publication rejects an unfinished changelog.
6. After verified publication, update the README's current-release table, TODO
   and compatibility record with the actual public versions and release links.

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked --directory packages/fastapi-streams python scripts/codegen.py
uv run --locked --directory packages/fastapi-rpckit python -m fastapi_rpckit.codegen.cli generate --config examples/generated_clients/rpcgen.toml
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
uv run --locked python scripts/check_distributions.py --python 3.12 --dependencies minimum
uv run --locked python scripts/check_streams_artifacts.py
uv run --locked python scripts/release.py validate --package fastapi-streams --version 0.2.0
```

The last command checks local metadata without claiming remote CI/publication
readiness. Minimum mode selects the lowest jointly satisfiable direct runtime
and extra dependencies; transitive dependencies resolve normally. See
[compatibility](compatibility.md) and [RPC consumer scope](rpc-parity.md).

## Dispatch a dry run

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=NEXT_VERSION -f dry_run=true
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-canon -f version=NEXT_VERSION -f dry_run=true
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-rpckit -f version=NEXT_VERSION -f dry_run=true
gh run list --repo mathisarends/canon --workflow release.yml --limit 10
```

Replace `NEXT_VERSION` with that package's prepared, unpublished version. The
current versions above are already published and cannot be dispatched as new
releases. Use the run IDs to inspect logs and artifacts. A dry run has no OIDC or repository
write permissions and creates no upload, release tag or GitHub release. The
publishing and finalization jobs are skipped.

Preparation validates package/version/tag, constants, pins, changelog, lockfile,
main ancestry, exact-commit successful push CI, existing tags and the public PyPI
version endpoint. New runs reject already published versions. Canonical
prereleases such as `0.1.0rc1` are supported; local/dev/post versions are rejected.

Only the selected package is built into `dist/release/`. Fresh environments test
those exact upload bytes with current dependencies and direct minima on Python
3.12, covering package combinations and installed Streams backends. Metadata,
CLIs, templates, sdists and typed markers are checked. Other libraries are built
as test dependencies and are excluded from the upload directory. Exact-commit CI
also covers source tests, types and client drift, including both RPC manifests.

Each run uploads `release-PACKAGE-VERSION`, containing `release/` and
`release-report/`. The JSON report records package, version, commit, tag, CI/run
links, checks and SHA-256 hashes; `release-notes.md` comes from its changelog.
Artifacts are retained for 90 days. Failed preparation artifacts can be replaced
on retry; publication requires successful preparation and matching hashes.

## Verified dry runs, 2026-10-17

All three runs completed successfully at commit
[`3d8c1de`](https://github.com/mathisarends/canon/commit/3d8c1de9eba123f6cd5f1667761c943f845e3c7e),
after its [complete CI run](https://github.com/mathisarends/canon/actions/runs/39044259386)
passed Linux/Python 3.12, 3.13 and 3.14 plus Windows/Python 3.14.

| Package | Version | Successful dry run |
| --- | --- | --- |
| Streams | 0.1.0 | [39044655537](https://github.com/mathisarends/canon/actions/runs/39044655537) |
| Canon | 0.5.0 | [39044659324](https://github.com/mathisarends/canon/actions/runs/39044659324) |
| RPC | 0.1.0 | [39044663425](https://github.com/mathisarends/canon/actions/runs/39044663425) |

Each passed metadata/CI gates, both artifact dependency profiles and the installed
Streams backend checks. Each downloaded artifact contains only the selected wheel
and sdist under `release/`, plus its manifest and changelog notes under
`release-report/`. Local verification recomputed every SHA-256 hash and confirmed
that none of the three versions exists on PyPI. Publication and finalization jobs
were skipped; no release tags or GitHub releases were created.

These runs verified preparation and artifact transfer. The first publications
below also verify OIDC upload and subsequent public-index installs.

## First publications, 2026-10-17

The user explicitly authorized all three publications. Streams was published
before Canon; RPC was released independently. All release runs finished successfully.

| Package | Version | PyPI | GitHub release | Workflow |
| --- | --- | --- | --- | --- |
| `fastapi-streams` | 0.1.0 | [Files](https://pypi.org/project/fastapi-streams/0.1.0/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.1.0) | [39045419743](https://github.com/mathisarends/canon/actions/runs/39045419743) |
| `fastapi-canon` | 0.5.0 | [Files](https://pypi.org/project/fastapi-canon/0.5.0/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.5.0) | [39046070906](https://github.com/mathisarends/canon/actions/runs/39046070906) |
| `fastapi-rpckit` | 0.1.0 | [Files](https://pypi.org/project/fastapi-rpckit/0.1.0/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-rpckit-v0.1.0) | [39045425324](https://github.com/mathisarends/canon/actions/runs/39045425324) |

Streams/RPC tags point to `c9b8219`, whose
[four-target CI](https://github.com/mathisarends/canon/actions/runs/39045136821)
passed. Canon points to `cd16e46`, whose
[four-target CI](https://github.com/mathisarends/canon/actions/runs/39045719895)
also passed. Each GitHub release attaches the original wheel, sdist and JSON
manifest. PyPI and downloaded file hashes match those manifests.

Each workflow passed fresh public-index runtime installs; Canon covered both
core-only and `[streams]`. Additional Windows/Python 3.14 verification installed
all three pinned public versions together, exercising HTTP/SSE/RPC, Dishka state
and cleanup, plus an RPC Python SDK roundtrip and TypeScript compilation.
Streams' public wheel also passed core-only, HTTPX and HTTPX2 CLI/client checks.
Public RPC 0.1.0 generated both SDKs for Cara's 15-method contract with drift,
import, compilation and Python Ruff checks passing. Cara's full service migration
is still open.

The first Streams/RPC attempts uploaded successfully but their post-upload gate
rejected PyPA's newly generated attestation sidecars. Rerunning only failed jobs
verified the original matching files without another upload. The workflow now
uses a separate upload staging directory. Because that workflow change advanced
`main`, GitHub required workflow-authorized credentials to create the older
release tags; the existing authorized CLI login completed those exact original
releases, and the original jobs then verified them successfully. Canon completed
the corrected workflow on its first attempt.

## Follow-up publications, 2026-10-18

The user explicitly authorized all three publications and their GitHub Releases.
Every package was published from final dated source
[`4af9092`](https://github.com/mathisarends/canon/commit/4af9092477ec3fb7a0224b9fea5242216859a37a),
after [four-target CI](https://github.com/mathisarends/canon/actions/runs/39127577804)
passed. Streams completed before Canon's new optional pin was published.

| Package | Version | PyPI | GitHub Release | Workflow |
| --- | --- | --- | --- | --- |
| `fastapi-streams` | 0.2.0 | [Files](https://pypi.org/project/fastapi-streams/0.2.0/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-streams-v0.2.0) | [39127849552](https://github.com/mathisarends/canon/actions/runs/39127849552) |
| `fastapi-rpckit` | 0.2.0 | [Files](https://pypi.org/project/fastapi-rpckit/0.2.0/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-rpckit-v0.2.0) | [39127851605](https://github.com/mathisarends/canon/actions/runs/39127851605) |
| `fastapi-canon` | 0.5.1 | [Files](https://pypi.org/project/fastapi-canon/0.5.1/) | [Notes and artifacts](https://github.com/mathisarends/canon/releases/tag/fastapi-canon-v0.5.1) | [39128242039](https://github.com/mathisarends/canon/actions/runs/39128242039) |

All release runs completed successfully. Each manifest records the exact source,
CI and artifact gates. Downloaded Actions wheel/sdist files, GitHub release assets
and PyPI SHA-256 digests agree. GitHub release notes match the exported changelogs;
every stable release is public, has exactly the original wheel, sdist and manifest
attached, and its package-prefixed tag resolves to `4af9092`.

Each workflow verified fresh public-index installs; Canon covered core-only and
`[streams]`. Additional public Streams CLI/SDK checks pass core-only, HTTPX and
HTTPX2 separately, including scalar constraints and unknown-event policy. Public
RPCkit 0.2.0 also passes both SDK generation, drift, compilation and Python Ruff
checks for Cara's 15-method contract; this does not establish its full service
migration. A fresh Windows/Python 3.14 virtual environment also installs all
three exact releases directly from PyPI and passes combined HTTP/SSE/RPC,
Dishka state/cleanup, an RPC Python SDK roundtrip and TypeScript compilation.
That environment resolves FastAPI 0.144.0, Pydantic 2.14.1 and Dishka 1.10.1.
Local downloaded evidence is under `dist/publications/`.

Streams' first post-upload install encountered temporary PyPI index visibility
lag. Rerunning only failed jobs on the original run verified the same existing
files, skipped another upload and created the matching GitHub Release. No
published contents were replaced and no existing tags were moved.

## Publish when explicitly authorized

Every package publication must include a matching GitHub Release in this
repository, with the package-prefixed tag at the verified source commit,
changelog notes, original wheel/sdist and release manifest. This is a standing
user preference, confirmed on 2026-10-18. Verify the release and all assets before
reporting completion; a successful PyPI upload alone is not a completed release.

After preparing a new version, finalizing its changelog and passing CI, dispatch
with `dry_run=false`. For a new Streams version:

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=NEXT_VERSION -f dry_run=false
```

The `publish` job uses environment `pypi` and job-scoped `id-token: write`.
It downloads the checked artifacts, verifies hashes and rejects conflicting PyPI
files. Copy only the verified wheel and sdist from `dist/release/` into
`dist/pypi-upload/` for Trusted Publishing. PyPA's action writes signature sidecars
beside its inputs, so that staging directory keeps the canonical artifacts
unchanged for subsequent hash checks. Canon publication also requires the pinned
Streams version to exist on PyPI.

After upload, verify public PyPI hashes and fresh public-index installs, including
Canon alone and `[streams]`. Only then does the separate `finish` job create the
package tag and GitHub release at the verified commit, attaching the original
artifacts and JSON report. Prereleases produce prerelease GitHub releases. Build
jobs cannot publish/create tags; the publishing job cannot write repository contents.

## Resume and record the outcome

- After a source fix, commit/push, pass CI and dispatch a new run. For a transient
  failure on the same source, use `gh run rerun RUN_ID --failed --repo mathisarends/canon`.
- After upload/finalization failure, rerun only failed jobs on the original run.
  That retains its verified artifacts and commit. Existing PyPI files must match
  the original manifest's names/hashes. Partial uploads send missing original
  files; complete uploads are verified without uploading again. Conflicts fail.
- A matching GitHub release is accepted on retry; tags at different commits are
  rejected. Do not move tags or rebuild changed contents under a published version.
- Keep root workflow files unchanged until a release finishes. If they change
  on `main` during a run, creating a release for the older workflow revision can
  require workflow-write authorization that `GITHUB_TOKEN` cannot receive. Use
  an already authorized CLI login with that permission to create the release at
  the manifest's exact commit, using its original notes, wheel, sdist and report;
  then rerun only the failed finalization job. See
  [GitHub's release API permission note](https://docs.github.com/en/rest/releases/releases#create-a-release).
- Record only verified publication/install outcomes in TODO, compatibility and
  release documentation. Cara's full application migration and predecessor
  archival remain separate work; archival needs explicit approval.

A successful dry run proves the preparation path. The first three explicitly
authorized releases also verified OIDC uploads and the post-publication path.
