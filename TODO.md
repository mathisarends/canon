# Release status and remaining migration work

Updated: 2026-10-18. This is the prioritized checklist for the next work block.
Completed migration steps are recorded in [docs/migration.md](docs/migration.md).

**Current scope:** The user authorized the initial publications on 2026-10-17
and the follow-up, SDK hardening and SDK efficiency publications with GitHub Releases on
2026-10-18. All three
packages are published on PyPI with matching GitHub releases
in this repository. The [README](README.md#current-releases) shows every current
package release. RPC is `fastapi-rpckit` / `fastapi_rpckit` after PyPI rejected the
initial `fastapi-wsrpc` name. Full external application migration remains open.

**Goal:** Release the three packages independently from `mathisarends/canon`
through a documented process that an agent can operate entirely through the CLI
and GitHub Actions when asked to prepare or publish a release.

## Active preparation: SDK review improvements

The user authorized preparation of Streams 0.4.0 and Canon 0.5.4 on 2026-10-18
and requested publication approval in this chat when ready. These are prepared
source versions, not published releases; RPCkit remains 0.2.0. Changelog dates
are finalized for review. Current public versions remain Streams 0.3.1 and
Canon 0.5.3 until separately authorized publication and verification.

- [x] Add SDK manifest provenance and checked optional HTTP-error decoder recipes.
- [x] Resolve release-note links against the release commit; correct the existing
  Canon 0.5.3 release body, preserving its original tag and artifact metadata.
- [x] Prepare independent versions, optional/development pins, root lockfile,
  regenerated clients and concrete migration notes.
- [x] Pass current/minimum wheel matrices and installed CLI/backends.
- [x] Pass final-version workspace checks: 1,463 Python tests, 23 TypeScript
  tests, lint/types and generated-client drift/coverage.
- [ ] Request explicit approval here before publication. Publish Streams before
  Canon and verify each PyPI install, tag, GitHub Release and original assets.

Before requesting approval, the final main commit must pass exact-source CI and
both package dry runs. Verify their downloaded wheel/sdist hashes, manifests and
absolute release-note links. Actions retains the source-specific results;
downloaded evidence belongs under `dist/dry-runs/`.

## Completed releases: SDK efficiency patches

Published and verified: Streams 0.3.1 and Canon 0.5.3; RPCkit stays 0.2.0.
The user explicitly authorized both publications with matching GitHub Releases
on 2026-10-18. Both releases have verified PyPI installs, tags, GitHub Releases
and original artifacts. See the [publication record](docs/releases.md#sdk-efficiency-publications-2026-10-18)
and [validation/performance decision](docs/design-decisions/0004-sdk-validation-efficiency.md).

- [x] Add repeatable Python/Node SDK benchmarks and measure the current runtime.
- [x] Cache Python ignore-policy setup and JSON-value adapters; defer details for
  skipped events while retaining strict known-event validation on both backends.
- [x] Extend optional diagnostic reports with schema/generator provenance and
  target-specific validation phases, preserving IDs and reviewed allowances.
- [x] Prepare independent patch versions, pins, root lockfile and upgrade notes.
- [x] Complete workspace and current/minimum installed-artifact checks, including
  both Streams backends and a Python 3.12 minimum-dependency generated SDK smoke.
  See [local verification](docs/compatibility.md#sdk-efficiency-patch-preparation).
- [x] Push final source `c9041d4`, pass all four CI targets and both package dry runs.
- [x] Obtain publication authorization and finalize both changelog dates.
- [x] Publish Streams before Canon with complete PyPI/tag/GitHub Release verification.
- [x] Independently match PyPI/Actions/GitHub bytes, tags, notes and manifests;
  pass public HTTPX2 SDK and combined three-package checks in fresh environments.

## External SDK adoption

- [x] Record the consumer-reported adoption of Canon 0.5.2, Streams 0.3.0 and
  RPCkit 0.2.0, including early request validation, structured errors and exact
  reviewed diagnostic allowances.
- [x] Record consumer-reported adoption of Streams 0.3.1 / Canon 0.5.3 with
  regenerated SDKs, unchanged callers/contracts, 19 exact TypeScript allowances
  and no Python diagnostics. Keep the selected HTTP backend on regeneration.
- [ ] Complete the consumer's native Hermes runtime and browser E2E validation.
  Record consumer-reported evidence separately from this workspace's checks.
- [ ] Turn new contract/validation failures into minimal schema fixtures and
  regression cases before preparing another independent package release.

The latest supplied Maximus report for merge request 125 confirms adoption of
Canon 0.5.3 / Streams 0.3.1 with regenerated SDKs and unchanged callers, HTTP/SSE
contracts and TypeScript SDK. It reports 317 Python tests passed, 14 native
Chromium tests skipped, frontend type checking and an SSE unit test passed, 19
exact reviewed TypeScript allowances, and an empty Python diagnostic report.
It also reports passing existing request/event/error/pool checks. No independent
performance benchmark, full Linux Hermes runtime or browser E2E was run there.
This is consumer-reported evidence, not locally verified application/deployment
coverage. See [the supplied review](https://git.fh-muenster.de/fep_ai_agent/maximus-trading/-/merge_requests/125#note_242680).

## Completed releases: generated SDK request validation and diagnostics

Authorized scope: implement directly on main and prepare Streams 0.3.0 and Canon
0.5.2. The user explicitly authorized publication with matching GitHub Releases
on 2026-10-18. Both are published and verified; RPCkit stays 0.2.0.

- [x] Validate Python path/query/header constraints at the method call while
  preserving valid serialization and existing body/event behavior.
- [x] Add source-located target-specific diagnostics, JSON reporting, strict CI
  policy and exact reviewed allowances; enforce the policy in drift checks.
- [x] Expose structured Python stream errors without automatic payload logging.
- [x] Add both-backend regressions, installed-wheel smoke coverage, validation
  matrix and consumer migration notes.
- [x] Pass workspace lint/types/tests and client drift/coverage gates, both
  current/minimum wheel matrices, isolated Streams backends and a minimum-version
  Python 3.12 generator/SDK smoke. See the compatibility preparation record.
- [x] Commit/push implementation `2d47c61` on main, pass exact-source four-target
  CI and both release dry runs; verify downloaded wheel/sdist hashes and manifests.
  See [SDK hardening preparation](docs/releases.md#sdk-hardening-preparation-2026-10-18).
- [x] Obtain explicit publication approval and finalize both changelog dates.
- [x] Pass final-source CI at `782d990`, publish Streams before Canon, and verify
  PyPI installs, tags, GitHub Releases, changelog notes and original artifacts.
- [x] Match PyPI, Actions and GitHub asset hashes and record the actual releases
  in README, compatibility and release documentation. See
  [SDK hardening publications](docs/releases.md#sdk-hardening-publications-2026-10-18).
- [x] Verify the public Streams HTTPX2 SDK/CLI and all three exact public package
  versions together in fresh Windows/Python 3.14 environments.

## Completed releases: consumer integration feedback

Published and verified: Streams 0.2.0, Canon 0.5.1 and RPCkit 0.2.0, each with
its own tag and GitHub Release. Streams was published before Canon's updated
optional pin. The next work block is the remaining external consumer migration.

- [x] Correct PyPI instructions, dependency examples and optional-extra diagnostics;
  add active-documentation checks to workspace lint and release validation.
- [x] Make package-root RPC FastAPI imports canonical; retain `RpcRoutes` and the
  existing nested imports. Add explicit `dishka_router` options and an executable
  authenticated `RpcRoutes` example with rejection and credential-expiry tests.
- [x] Preserve supported scalar constraints in generated Python models and
  diagnose unsupported rules; document the stricter SDK migration.
- [x] Add explicit unknown-event ignoring for top-level discriminated Python SSE
  unions, retaining strict known-event validation and both HTTP backends.
- [x] Add tested native-proxy and private REST-codegen compatibility recipes.
- [x] Pass all workspace, current/minimum wheel and installed Streams backend
  gates, including new generated validation/unknown-event smoke checks.
- [x] Push prepared commit `de05d8c`, pass [four-target CI](https://github.com/mathisarends/canon/actions/runs/39126069250)
  and all three release dry runs. Downloaded artifacts match their manifest hashes;
  see [verified follow-up preparation](docs/releases.md#verified-follow-up-preparation-2026-10-18).
- [x] Record the pre-1.0 breaking-change policy in agent/release guidance and
  release validation; correct RPCkit to 0.2.0. The previous 0.1.1 dry run is
  historical and cannot validate the corrected version.
- [x] Pass [four-target CI](https://github.com/mathisarends/canon/actions/runs/39126936002)
  and the [RPCkit 0.2.0 dry run](https://github.com/mathisarends/canon/actions/runs/39127145156)
  at `0a2b097`; downloaded artifact hashes match the manifest.
- [x] Obtain explicit publication authorization on 2026-10-18 and finalize the
  three changelog dates. Every publication must include a verified GitHub Release.
- [x] Pass [four-target CI](https://github.com/mathisarends/canon/actions/runs/39127577804)
  on the final dated source commit `4af9092`.
- [x] Publish Streams 0.2.0, RPCkit 0.2.0 and then Canon 0.5.1 after Streams.
- [x] Verify PyPI installs, matching tags, GitHub Releases and original assets;
  update the current-release and compatibility records. See
  [publication evidence](docs/releases.md#follow-up-publications-2026-10-18).

The [consumer feedback decision](docs/design-decisions/0002-consumer-feedback.md)
records scope and remaining limits. Maximus feedback is consumer-reported evidence;
this workspace does not claim a locally verified full Maximus or Cara migration.

## Completed

- [x] Consolidated `packages/fastapi-canon`, `packages/fastapi-streams`, and
  `packages/fastapi-rpckit`, preserving their source histories.
- [x] Established a shared uv workspace, root lockfile, and separate package test processes.
- [x] Renamed the RPC successor to `fastapi-rpckit` / `fastapi_rpckit`;
  FastAPI is required, and the existing RPC engine is retained.
- [x] Tested HTTP/SSE/RPC together with Dishka, including installed wheels.
- [x] Migrated the reference service to actual Canon composition and Problem Details.
- [x] Passed CI on Linux/Python 3.12–3.14 and Windows/Python 3.14,
  including the reference service migration:
  [verified commit `9dddd21`](https://github.com/mathisarends/canon/actions/runs/39031639556).
- [x] Updated the GitHub description/topics and the profile README in `../mathisarends`.

## 1. Decide release scope and versions

The PyPI versions were checked directly on 2026-10-17:

| Distribution | Workspace version | PyPI | Next action |
| --- | --- | --- | --- |
| `fastapi-canon` | `0.5.0` | [0.5.0](https://pypi.org/project/fastapi-canon/0.5.0/) | Published and installed independently, with and without Streams. |
| `fastapi-streams` | `0.1.0` | [0.1.0](https://pypi.org/project/fastapi-streams/0.1.0/) | Published; CLI, generated clients and both HTTP backends verified. |
| `fastapi-rpckit` | `0.1.0` | [0.1.0](https://pypi.org/project/fastapi-rpckit/0.1.0/) | Published; both SDKs verified for Cara's contract; full application migration remains. |

- [x] Review changes since each published version and choose target versions.
  Canon adds `CanonStreamRouter` and `HTTPMethod`; Streams includes changes to
  generated types, error aliases, and SDK documentation. Review the Streams
  changelog for required client migrations as well.
  Chosen versions are Canon 0.5.0, Streams 0.1.0 and RPC 0.1.0; the published
  Canon/Streams wheels were compared directly. See [release scope](docs/releases.md).
- [x] Publish the new Canon/Streams contents under new versions; do not reuse
  existing published versions for changed builds.
- [x] Update each affected package's `pyproject.toml`, changelog, and, for
  Streams/RPC, `__version__`. Canon currently obtains its distribution version
  from package metadata.
- [x] Update dependent pins together: the root `pyproject.toml`, Canon's `streams`
  extra and development group, and the root `uv.lock`.
- [x] Update the reference service to `fastapi-canon>=0.5,<0.6` and verify its
  five tests against the independently installed Canon 0.5.0 wheel.
- [x] Point Canon/Streams package URLs to the new development repository and
  appropriate package/documentation subdirectories.
- [x] Regenerate example clients after version/generator changes and run their
  drift checks, including the RPC generator manifests.

**Order:** Prepare target versions and release changes together. Publish Streams
before a Canon release that requires its new version. RPC can be released
independently. Do not force a shared version number.

RPC's first release is 0.1.0. The 0.11.0 predecessor engine is
preserved, and the consumer check found a Python generator formatting issue that
is fixed with a regression test. Regeneration leaves the current example outputs
and RPC manifests unchanged; drift checks confirm them.

## 2. One-time account setup by Mathis

These settings were configured and verified on 2026-10-17 and match the root
release workflow. The PyPI setup used the user's signed-in session without
reading passwords, API tokens or cookies; GitHub setup used its existing CLI login.

| Publisher field | Configured value |
| --- | --- |
| GitHub Owner | `mathisarends` |
| Repository | `canon` |
| Workflow file | `release.yml` under `.github/workflows/` |
| GitHub Environment | `pypi` |

- [x] For **both existing PyPI projects**, `fastapi-canon` and `fastapi-streams`,
  check the Trusted Publisher for this monorepo and add it if needed. Publishers
  configured for the old repositories do not configure publishing from `canon`.
  [Existing project instructions](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
- [x] For `fastapi-rpckit`, check name acceptance and configure/check a
  **Pending Publisher** for the new project. The first successful publication
  creates the project; a pending publisher does not reserve its name.
  [New project instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
  PyPI accepted the pending publisher and the first OIDC upload created the
  `fastapi-rpckit` project. It rejected `fastapi-wsrpc` as too similar to an existing
  project, so the user selected `fastapi-rpckit`.
- [x] Configure the GitHub `pypi` environment and allowed release refs. Decide
  whether publication also requires an environment reviewer. Document the policy
  so an agent can tell whether human approval in GitHub is still pending after dispatch.
  Only `main` may deploy. No extra environment reviewer or wait timer is configured;
  explicit manual dispatch and release gates control publication.
- [x] Ensure that an agent authorized to perform a release has the necessary
  repository/Actions write access. Use GitHub OIDC for PyPI authentication;
  persistent PyPI tokens are not required for that flow.
- [ ] Decide when the old repositories should stop producing their own package
  releases. Keep the repositories and historical tags available for now.

## 3. Implement a release process agents can operate

Implemented after the user authorized setup. The workflow is manually dispatched
from `main`, defaults to a dry run, and keeps OIDC/repository write permissions
out of its build job.

**Current state:** The root has `ci.yml` and `release.yml`.
The `.github` directories under `packages/` are imported, inactive legacy
configuration. In particular, the old Streams release check expects `vX.Y.Z`
and a package-local lockfile; it cannot serve as the monorepo release gate unchanged.

- [x] Implement an explicit mapping of distribution, directory, import name,
  version, and tag prefix. Release checks should read this metadata without
  importing package business modules.
- [x] Allow only the three libraries as release targets; do not publish
  `canon-workspace` or the development reference service as stack packages.
- [x] Document package-specific tag names (no tags created):
  `fastapi-canon-vX.Y.Z`, `fastapi-streams-vX.Y.Z`, `fastapi-rpckit-vX.Y.Z`.
- [x] Build a shared release check: package, tag, and version must agree;
  metadata, existing version constants, changelog, and root lockfile must be
  consistent. The release commit must be on `origin/main`, and that exact commit
  must have passed the required checks.
- [x] Add `.github/workflows/release.yml` with explicit package selection,
  a version input, `workflow_dispatch`, and a real dry run. A dry run checks and
  builds artifacts without changing PyPI, release tags, or GitHub releases.
  [GitHub CLI/dispatch documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
- [x] Limit publication to the selected package and its freshly built artifacts;
  do not upload old or unrelated wheels from a shared `dist/` directory.
  Prevent concurrent releases of the same package version and detect already
  published versions explicitly before uploading.
- [x] Configure the publishing job with `environment: pypi` and job-scoped
  `id-token: write`. Regular PR/CI jobs do not need publishing permissions.
- [x] Check local wheels/sdists, metadata, `py.typed`, templates, CLI entry
  points, installed smoke consumers and both generated SDKs.
- [x] Wire those artifact gates into publication and publish only the artifacts
  that passed the checks.
- [x] Provide machine-readable results and clear errors: package, version,
  commit, tag, checks, artifact hashes, and workflow/PyPI links. Document how to
  resume after a failed run.
- [x] Extend `docs/releases.md` and `AGENTS.md` with the complete workflow:
  prepare a release, update versions, run checks, commit/open a PR, start a dry
  run, publish when authorized, and verify the result. An agent should not have
  to infer old repository workflows or undocumented upload procedures.

**Implemented CLI interface:**

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=NEXT_VERSION -f dry_run=true
```

`NEXT_VERSION` is a placeholder; the prepared Streams version is `0.1.0`. When
asked to release, an agent should be able to use the same documented process
for publication under the configured GitHub rules.

## 4. Complete verification before the first publication

- [x] Test direct minimum dependencies and the newest compatible versions outside the
  workspace: Canon alone, Streams alone, RPC alone, and supported combinations.
  The full stack has a different lower bound from Canon alone because Streams
  requires at least FastAPI `0.143.3`.
  Six fresh wheel environments per profile pass runtime/codegen smoke checks;
  minima use Python 3.12 and latest uses Python 3.14. This does not claim every
  transitive minimum or exhaustive dependency permutations.
- [x] Record tested package versions and dependency ranges in
  [docs/compatibility.md](docs/compatibility.md). The shared lockfile does not
  replace these consumer checks.
- [x] Select a real RPC consumer: Cara Gateway; audit its existing imports and
  exported OpenRPC contract against the successor. See [RPC parity](docs/rpc-parity.md).
- [ ] Complete Cara's full application migration and run installation,
  mounting, Dishka, authentication, subscription and voice/media tests there.
  Cara still pins pyrpckit 0.8.0; its old module paths need explicit migration.
- [x] Check generated Python/TypeScript clients against that consumer's exported
  contract and update the [RPC migration guide](packages/fastapi-rpckit/docs/migration.md)
  with required changes. Both SDKs for Cara's 15-method contract pass generation,
  drift and compilation; Python also passes package import and Ruff lint/format.
- [x] Pass a complete dry run for each package intended for publication:
  [Streams 0.1.0](https://github.com/mathisarends/canon/actions/runs/39044655537),
  [Canon 0.5.0](https://github.com/mathisarends/canon/actions/runs/39044659324), and
  [RPC 0.1.0](https://github.com/mathisarends/canon/actions/runs/39044663425).
  All use commit `3d8c1de`, whose complete Linux/Windows CI passed. Downloaded
  wheel/sdist hashes match each manifest. Publishing/finalization jobs were
  skipped; no PyPI uploads, release tags or GitHub releases were created.

These existing root commands already work:

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
uv run --locked python scripts/check_distributions.py --python 3.12 --dependencies minimum
uv run --locked python scripts/check_streams_artifacts.py
```

## 5. Publish and verify

- [x] Publish the new Streams version, install it from PyPI in a fresh
  environment, and check its CLI and generated clients.
- [x] Publish the new Canon version with the matching optional Streams
  dependency; check both core-only and `fastapi-canon[streams]` installs from PyPI.
- [x] Publish `fastapi-rpckit` for the first time, verify its public files/installs,
  and compile both SDKs for Cara's 15-method contract using the PyPI version.
- [ ] Migrate Cara's full application to the PyPI version. Claim consumer
  migrations only after they are complete.
- [x] Update GitHub release notes, changelogs, installation examples, and the
  compatibility record to reflect the versions actually available.
- [ ] Add a clear notice linking to the new development repository in the old
  repositories. Keep them available as agreed. Archive `pyrpckit` only after the
  replacement is proven and a later explicit decision authorizes archival.

**Release publication is complete:** all three packages have independent releases,
verified public-index installs, matching tags/artifacts and documented CLI recovery.
Full external application migration and old-repository decisions remain follow-up
work. See [publication evidence](docs/releases.md#first-publications-2026-10-17).

## Later, after the first releases

- [ ] Expand the agent-run/remote-browser examples around real consumers.
- [ ] Change RPC ergonomics only when concrete needs justify it; do not add a
  new router/protocol abstraction solely because the package was renamed.
- [ ] Evaluate optional scaffolding/templates and an installable stack snapshot
  or constraints file.
- [ ] Extract shared codegen helpers only when stable reuse exists; do not
  introduce a mandatory shared runtime in advance.

## Starting prompt for the next agent

> Read TODO.md and the linked release/compatibility and RPC parity documents.
> All three initial releases are published and verified; the README links their
> PyPI versions and central GitHub releases. Remaining work includes Cara's full
> application migration and decisions about the old repositories. Future releases
> need new versions and explicit publication authorization. Keep publication and
> verified consumer migration separate in reports.
