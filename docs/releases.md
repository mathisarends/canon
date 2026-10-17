# Independent releases

Release one library at a time from `mathisarends/canon`. The root workspace and
reference service are not publication targets. No package has yet been published
through this repository's new workflow.

## Prepared versions

| Distribution | Import | Version | Tag |
| --- | --- | --- | --- |
| `fastapi-streams` | `fastapi_streams` | 0.1.0 | `fastapi-streams-v0.1.0` |
| `fastapi-canon` | `fastapi_canon` | 0.5.0 | `fastapi-canon-v0.5.0` |
| `fastapi-rpckit` | `fastapi_rpckit` | 0.1.0 | `fastapi-rpckit-v0.1.0` |

Publish Streams before Canon: Canon's `streams` extra pins Streams 0.1.0.
RPC is independent. The last published Canon/Streams versions are 0.4.0/0.0.1;
changed builds require new versions. Follow the Streams changelog's generated
literal/enum and error-alias migration. Versions do not need to match.

`release.toml` maps distributions, directories, modules and tag prefixes. Versions
come from package metadata; the release check does not import business modules.

## Account configuration verified on 2026-10-17

| PyPI project | Publisher state |
| --- | --- |
| `fastapi-canon` | Trusted Publisher configured and verified |
| `fastapi-streams` | Trusted Publisher configured and verified |
| `fastapi-rpckit` | Pending Publisher accepted and verified |

All use GitHub owner `mathisarends`, repository `canon`, workflow filename
`release.yml`, and environment `pypi`. No persistent PyPI token is needed. The
GitHub environment allows only `main`. No additional reviewer or wait timer is
configured: publication uses manual dispatch and the gates below. Agents still
need explicit user authorization to dispatch a real publication.

PyPI rejected the initial `fastapi-wsrpc` name as too similar to an existing
project. The user selected `fastapi-rpckit` / `fastapi_rpckit`, and PyPI accepted
its pending publisher. This does not reserve the name or create the project;
the first successful upload does that. See
[PyPI's pending publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Prepare a version

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

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked --directory packages/fastapi-streams python scripts/codegen.py
uv run --locked --directory packages/fastapi-rpckit python -m fastapi_rpckit.codegen.cli generate --config examples/generated_clients/rpcgen.toml
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
uv run --locked python scripts/check_distributions.py --python 3.12 --dependencies minimum
uv run --locked python scripts/check_streams_artifacts.py
uv run --locked python scripts/release.py validate --package fastapi-streams --version 0.1.0
```

The last command checks local metadata without claiming remote CI/publication
readiness. Minimum mode selects the lowest jointly satisfiable direct runtime
and extra dependencies; transitive dependencies resolve normally. See
[compatibility](compatibility.md) and [RPC consumer scope](rpc-parity.md).

## Dispatch a dry run

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=0.1.0 -f dry_run=true
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-canon -f version=0.5.0 -f dry_run=true
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-rpckit -f version=0.1.0 -f dry_run=true
gh run list --repo mathisarends/canon --workflow release.yml --limit 10
```

Use the run IDs to inspect logs and artifacts. A dry run has no OIDC or repository
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

These runs verify preparation and artifact transfer. OIDC upload and subsequent
public-index verification remain untested until an authorized publication.

## Publish when explicitly authorized

After finalizing the changelog and passing CI, dispatch with `dry_run=false`.
The first real publication will be Streams:

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-streams -f version=0.1.0 -f dry_run=false
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
- Record only verified publication/install outcomes in TODO, compatibility and
  release documentation. Cara's full application migration and predecessor
  archival remain separate work; archival needs explicit approval.

A successful dry run proves the preparation path. The actual OIDC upload and
post-publication path are verified by the first explicitly authorized release.
