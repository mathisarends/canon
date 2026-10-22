# Independent releases

Release the four libraries independently from `mathisarends/canon`. The workspace
and reference service are not publication targets. `release.toml` maps package
names, directories, modules and tag prefixes; `scripts/release.py` validates them.
Published versions and their GitHub/PyPI assets are listed in the
[README](../README.md#current-releases). Package changelogs contain migration notes;
GitHub Releases and Actions retain publication evidence.

## Current versions

These consumer integration versions were published on 2026-10-20 from
[verified source `7568df7`](https://github.com/mathisarends/canon/commit/7568df705bfba6b6165249734fa0a1f5dd768a1f).
Each package has a matching tag and GitHub Release with its original wheel, sdist
and manifest. PyPI file hashes, public installs and release assets are verified.

| Package | Version | Migration |
| --- | --- | --- |
| Canon | 0.6.0 | Use the optional `[webrtc]` extra and `CanonWebRtcRouter` for registry-backed admission errors; declare dependency/factory failures with `raises`. |
| WebRTC | 0.2.0 | Forward the new admission-provider keyword in router overrides and regenerate clients. Session engine bindings and browser media observation are optional. |
| RPCKit | 0.4.0 | Regenerate Python clients and invoke factory protocols with positional URLs. Handle `CancelledError` when cancelling direct `serve_websocket()` calls. |

Streams remains at published 0.4.0. WebRTC must be available before publishing a
Canon version that pins it in the optional extra. RPCKit releases independently.
Apply the same dependency order when a Canon version pins a new Streams release.

### Consumer integration upgrade

This batch addresses the integration feedback for Canon 0.5.5, WebRTC 0.1.0 and
RPCKit 0.3.0:

- [Canon admission errors](../packages/fastapi-canon/docs/webrtc.md) reuse named
  errors, validate registry membership and export declared dependency/factory
  failures in session contracts. HTTP denials happen before peer allocation;
  accepted sessions retain WebRTC protocol errors.
- [Remote engine bindings and leases](../packages/fastapi-webrtc/examples/remote_video/README.md)
  keep each viewer's resources independent, including cancellation and rejected
  second viewers. The example documents native error mapping and partial stats.
- [Browser video health](../packages/fastapi-webrtc/docs/media-health.md) observes
  decoded or compositor frames with optional first-frame and stall deadlines.
  Applications retain control of playback and fallback. The optional
  [HTTP ticket recipe](../packages/fastapi-webrtc/docs/admission-tickets.md) provides
  readable admission errors before signaling.
- [RPCKit factory typing](../packages/fastapi-rpckit/CHANGELOG.md#040---2026-10-20)
  removes the URL-parameter and backend subprotocol mismatches. Regenerate clients
  before removing consumer generator overrides.

The signaling protocol stays `fastapi-webrtc.v1`. A maintained CDP binding and
deployed TURN/NAT, database concurrency and proxy validation remain separate work.

## Publisher setup

Trusted Publishers use GitHub owner `mathisarends`, repository `canon`, workflow
filename `release.yml` and environment `pypi`. The environment permits `main`.
Publishing uses job-scoped OIDC; no persistent PyPI token is needed. Only root
workflows are active. Every real publication requires explicit user authorization.

## Prepare a version

Before 1.0, breaking changes advance `0.x.y` to `0.(x+1).0`. Patch versions are
for backward-compatible fixes and documentation. Public signatures, accepted
inputs, stricter validation, defaults and generated-client contracts count even
when wire formats do not change. Use a `### Breaking changes` changelog heading
with concrete migration steps. Release validation enforces the next minor and
patch zero for declared breaking changes.

1. Update the package version, changelog and existing `__version__` constant.
   Canon reads its version from installed metadata.
2. Update root pins, Canon's optional integration/development pins and the
   reference service's Canon range as needed. Run `uv lock` at the root.
3. Regenerate clients through their generators. Run the workspace, browser,
   current/minimum wheel and installed CLI checks in [contributing](contributing.md).
4. Commit/merge to `main` and wait for the complete `ci.yml` push run on that exact
   commit. Then dispatch the selected package's dry run.
5. Before an authorized publication, finalize the changelog heading as
   `## VERSION - YYYY-MM-DD`, commit/push and pass exact-source CI again.

Local metadata validation does not establish remote publication readiness:

```console
uv run --locked python scripts/release.py validate --package fastapi-webrtc --version NEXT_VERSION
```

## Dispatch a dry run

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-webrtc -f version=NEXT_VERSION -f dry_run=true
gh run list --repo mathisarends/canon --workflow release.yml --limit 10
```

Choose the package and its prepared, unpublished version. Use the workflow filename
without `.github/workflows/`. Canonical prereleases are supported; local/dev/post
versions are not. A new run rejects a version already on PyPI.

Preparation verifies metadata, constants, pins, changelog, lockfile, main ancestry,
exact-commit CI, tags and PyPI state. Only the selected wheel/sdist enters
`dist/release/`; other packages are built as test dependencies. Fresh environments
exercise those upload artifacts with current dependencies and direct minima on
Python 3.12, plus installed Streams/WebRTC CLI and generated-client checks.

Each run uploads `release-PACKAGE-VERSION` containing `release/` and
`release-report/`: the package/version/commit/tag, CI/run links, check results,
SHA-256 hashes and changelog-derived notes. Artifacts are retained for 90 days.
Dry runs have neither OIDC nor repository write permissions and skip publication
and finalization. Preparation artifacts can be replaced on a preparation retry;
publication uses the successful run's original verified bytes.

## Publish when explicitly authorized

After final changelog dates and exact-source CI, dispatch the selected package
with `dry_run=false` only when publication is explicitly authorized:

```console
gh workflow run release.yml --repo mathisarends/canon --ref main -f package=fastapi-webrtc -f version=NEXT_VERSION -f dry_run=false
```

The `publish` job downloads and verifies the prepared artifacts and uploads only
the wheel/sdist from a separate staging directory. Signature sidecars created by
the publisher must not modify the canonical artifact directory. Existing PyPI
files must match the original manifest; conflicting contents fail. Canon also
requires the pinned Streams and WebRTC versions to be available first.

After upload, verify hashes and fresh public-index installs. Canon checks core,
`[streams]`, `[webrtc]` and both extras together. The separate `finish` job then
creates the package-prefixed tag and central GitHub Release at the verified
commit, with changelog notes, original wheel/sdist and manifest attached.
Prereleases produce prerelease GitHub Releases. A PyPI-only upload is incomplete.

## Resume and record the outcome

- A source fix requires a new commit, exact-source CI and a new run. Retry a
  transient failure on unchanged source with
  `gh run rerun RUN_ID --failed --repo mathisarends/canon`.
- After upload/finalization failure, rerun only failed jobs on the original run.
  Partial uploads send missing original files; complete uploads are verified
  without reuploading. Never rebuild under a published version or move a tag.
- Matching releases are accepted on retry; a tag at another commit is rejected.
- Keep root workflows unchanged until a release finishes. If they change, an
  older source's release can require an already authorized CLI login with
  workflow-write permission. Use the manifest's exact commit, original notes,
  wheel, sdist and report, then retry finalization. See
  [GitHub's release API permission note](https://docs.github.com/en/rest/releases/releases#create-a-release).
- After verified publication, update the README's current versions and
  compatibility table. Keep per-run logs, manifests and checksums in Actions and
  the matching GitHub Release rather than adding development transcripts here.
