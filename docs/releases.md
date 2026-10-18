# Independent releases

Release one library at a time from `mathisarends/canon`. All three libraries have
published releases from this repository. The root workspace and reference service
are not publication targets. The [README](../README.md#current-releases) lists all
current package versions with PyPI and GitHub release links.

## Current released versions

| Distribution | Import | Version | Tag |
| --- | --- | --- | --- |
| `fastapi-streams` | `fastapi_streams` | 0.1.0 | `fastapi-streams-v0.1.0` |
| `fastapi-canon` | `fastapi_canon` | 0.5.0 | `fastapi-canon-v0.5.0` |
| `fastapi-rpckit` | `fastapi_rpckit` | 0.1.0 | `fastapi-rpckit-v0.1.0` |

Publish Streams before Canon: Canon's `streams` extra pins Streams 0.1.0.
RPC is independent. These Canon/Streams releases replace 0.4.0/0.0.1;
changed builds require new versions. Follow the Streams changelog's generated
literal/enum and error-alias migration. Versions do not need to match.

`release.toml` maps distributions, directories, modules and tag prefixes. Versions
come from package metadata; the release check does not import business modules.

## Prepared follow-up releases, 2026-10-18

| Package | Prepared version | Scope |
| --- | --- | --- |
| Streams | 0.2.0 | Scalar validation preservation, unsupported-rule diagnostics, opt-in unknown-event ignoring, native/mixed-codegen recipes. |
| Canon | 0.5.1 | Streams 0.2.0 optional/development pin and corrected integration guidance. |
| RPCkit | 0.2.0 | Breaking Dishka signature/context clarification, authenticated example and canonical FastAPI documentation. |

These are unpublished source versions. Streams' regenerated Python SDKs may reject
payloads that previously passed because constraints were dropped; read its
changelog before regeneration. Publish Streams before Canon. RPCkit keeps wire
contracts, `RpcRoutes` and existing nested imports. Changelog dates remain
unreleased until publication is authorized. Local checks and CI/dry-run evidence
are recorded in TODO and the compatibility record as they complete.

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
not a publication or verification of 0.2.0. Sources remain unreleased.

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

## Publish when explicitly authorized

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
