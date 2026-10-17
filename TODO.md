# Next work block: releases from the Canon monorepo

Updated: 2026-10-17. This is the prioritized checklist for the next work block.
Completed migration steps are recorded in [docs/migration.md](docs/migration.md).

**Current scope:** CI/release-workflow setup is deferred at the user's request
(2026-10-17). Local version preparation, RPC parity/consumer-contract checks and
artifact verification are recorded below. Publication and account setup remain
open; checked preparation items do not mean the packages are published.

**Goal:** Release the three packages independently from `mathisarends/canon`
through a documented process that an agent can operate entirely through the CLI
and GitHub Actions when asked to prepare or publish a release.

## Completed

- [x] Consolidated `packages/fastapi-canon`, `packages/fastapi-streams`, and
  `packages/fastapi-wsrpc`, preserving their source histories.
- [x] Established a shared uv workspace, root lockfile, and separate package test processes.
- [x] Renamed the RPC successor to `fastapi-wsrpc` / `fastapi_wsrpc`;
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
| `fastapi-canon` | `0.5.0`, prepared/unreleased | `0.4.0` | Publish after Streams and release setup. |
| `fastapi-streams` | `0.1.0`, prepared/unreleased | `0.0.1` | Publish after release setup; consumer migrations are documented. |
| `fastapi-wsrpc` | `0.1.0`, prepared/unpublished | JSON endpoint returns 404 | Confirm PyPI acceptance/publisher, then publish the first successor release. |

- [x] Review changes since each published version and choose target versions.
  Canon adds `CanonStreamRouter` and `HTTPMethod`; Streams includes changes to
  generated types, error aliases, and SDK documentation. Review the Streams
  changelog for required client migrations as well.
  Chosen versions are Canon 0.5.0, Streams 0.1.0 and RPC 0.1.0; the published
  Canon/Streams wheels were compared directly. See [release scope](docs/releases.md).
- [ ] Publish the new Canon/Streams contents under new versions; do not reuse
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

RPC retains its first unpublished 0.1.0 version. The 0.11.0 predecessor engine is
preserved, and the consumer check found a Python generator formatting issue that
is fixed with a regression test. Regeneration leaves the current example outputs
and RPC manifests unchanged; drift checks confirm them.

## 2. One-time account setup by Mathis

These settings belong to the GitHub/PyPI accounts; their configuration has not
yet been verified in this repository. Confirm that the proposed settings below
match the implemented workflow before configuring them:

| Publisher field | Proposed value |
| --- | --- |
| GitHub Owner | `mathisarends` |
| Repository | `canon` |
| Workflow file | `release.yml` under `.github/workflows/` |
| GitHub Environment | `pypi` |

- [ ] For **both existing PyPI projects**, `fastapi-canon` and `fastapi-streams`,
  check the Trusted Publisher for this monorepo and add it if needed. Publishers
  configured for the old repositories do not configure publishing from `canon`.
  [Existing project instructions](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
- [ ] For `fastapi-wsrpc`, check name acceptance and configure/check a
  **Pending Publisher** for the new project. The first successful publication
  creates the project; a pending publisher does not reserve its name.
  [New project instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
  The public endpoint still returns 404. The account publishing page redirects
  to login, so acceptance and Pending Publisher state remain unverified. The
  intended fields are documented in [the release guide](docs/releases.md).
- [ ] Configure the GitHub `pypi` environment and allowed release refs. Decide
  whether publication also requires an environment reviewer. Document the policy
  so an agent can tell whether human approval in GitHub is still pending after dispatch.
- [ ] Ensure that an agent authorized to perform a release has the necessary
  repository/Actions write access. Use GitHub OIDC for PyPI authentication;
  persistent PyPI tokens are not required for that flow.
- [ ] Decide when the old repositories should stop producing their own package
  releases. Keep the repositories and historical tags available for now.

## 3. Implement a release process agents can operate

Deferred: the user will handle CI/release-workflow setup later. No workflow or
GitHub environment was changed during this preparation.

**Current state:** The root has only `ci.yml`, with no publishing workflow.
The `.github` directories under `packages/` are imported, inactive legacy
configuration. In particular, the old Streams release check expects `vX.Y.Z`
and a package-local lockfile; it cannot serve as the monorepo release gate unchanged.

- [ ] Implement an explicit mapping of distribution, directory, import name,
  version, and tag prefix. Release checks should read this metadata without
  importing package business modules.
- [ ] Allow only the three libraries as release targets; do not publish
  `canon-workspace` or the development reference service as stack packages.
- [x] Document package-specific tag names (no tags created):
  `fastapi-canon-vX.Y.Z`, `fastapi-streams-vX.Y.Z`, `fastapi-wsrpc-vX.Y.Z`.
- [ ] Build a shared release check: package, tag, and version must agree;
  metadata, existing version constants, changelog, and root lockfile must be
  consistent. The release commit must be on `origin/main`, and that exact commit
  must have passed the required checks.
- [ ] Add `.github/workflows/release.yml` with explicit package selection,
  a version input, `workflow_dispatch`, and a real dry run. A dry run checks and
  builds artifacts without changing PyPI, release tags, or GitHub releases.
  [GitHub CLI/dispatch documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
- [ ] Limit publication to the selected package and its freshly built artifacts;
  do not upload old or unrelated wheels from a shared `dist/` directory.
  Prevent concurrent releases of the same package version and detect already
  published versions explicitly before uploading.
- [ ] Configure the publishing job with `environment: pypi` and job-scoped
  `id-token: write`. Regular PR/CI jobs do not need publishing permissions.
- [x] Check local wheels/sdists, metadata, `py.typed`, templates, CLI entry
  points, installed smoke consumers and both generated SDKs.
- [ ] Wire those artifact gates into publication and publish only the artifacts
  that passed the checks.
- [ ] Provide machine-readable results and clear errors: package, version,
  commit, tag, checks, artifact hashes, and workflow/PyPI links. Document how to
  resume after a failed run.
- [ ] Extend `docs/releases.md` and `AGENTS.md` with the complete workflow:
  prepare a release, update versions, run checks, commit/open a PR, start a dry
  run, publish when authorized, and verify the result. An agent should not have
  to infer old repository workflows or undocumented upload procedures.

**Proposed CLI interface — not implemented yet:**

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=NEXT_VERSION -f dry_run=true
```

The workflow must be implemented first; `NEXT_VERSION` is a placeholder. When
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
  contract and update the [RPC migration guide](packages/fastapi-wsrpc/docs/migration.md)
  with required changes. Both SDKs for Cara's 15-method contract pass generation,
  drift and compilation; Python also passes package import and Ruff lint/format.
- [ ] Pass a complete dry run for each package intended for publication.

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

- [ ] Publish the new Streams version, install it from PyPI in a fresh
  environment, and check its CLI and generated clients.
- [ ] Publish the new Canon version with the matching optional Streams
  dependency; check both core-only and `fastapi-canon[streams]` installs from PyPI.
- [ ] Publish `fastapi-wsrpc` for the first time and migrate the selected
  consumer to the PyPI version. Claim consumer migrations only after they are complete.
- [ ] Update GitHub release notes, changelogs, installation examples, and the
  compatibility record to reflect the versions actually available.
- [ ] Add a clear notice linking to the new development repository in the old
  repositories. Keep them available as agreed. Archive `pyrpckit` only after the
  replacement is proven and a later explicit decision authorizes archival.

**This work block is complete when** all three packages can be released
individually from this repository, the agent workflow is documented and proven,
and the planned releases have been verified through PyPI installs. Until then,
workspace consolidation is complete, but the release migration remains open.

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
> Versions and local preparation gates are ready. CI/release-workflow setup was
> deferred by the user; resume it only when requested. Remaining release work
> includes account/publisher setup, a root workflow and dry runs, a full external
> consumer migration, and explicitly authorized publication. Keep preparation,
> publication and verified consumer migration separate in status reports.
