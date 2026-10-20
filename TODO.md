# Next work

Updated: 2026-10-20. Keep this list limited to open work. Published versions are
listed in the [README](README.md#current-releases); completed work and evidence
belong in [migration](docs/migration.md), [releases](docs/releases.md) and
[compatibility](docs/compatibility.md).

## Current priority

- [ ] Merge the release preparation for WebRTC 0.1.0, RPCkit 0.3.0 and Canon
  0.5.5, then pass exact-commit CI and each package's release dry run on `main`.
  WebRTC PR #7 and RPCkit PRs #4, #5 and #6 are merged. Streams remains 0.4.0.
- [ ] Confirm WebRTC's PyPI Pending Publisher using the exact fields in
  [the release procedure](docs/releases.md#webrtc-first-publication-setup).
  GitHub's `pypi` environment already allows `main`; PyPI's private publishing
  page returned HTTP 503 during the 2026-10-20 audit, so registration is unverified.
- [ ] Obtain explicit publication authorization for the three prepared versions,
  then verify each PyPI install, tag, GitHub Release and original attached assets.
  Prepared source versions and dated changelogs are not published releases.

## External consumers

- [ ] Complete Cara Gateway's application migration from pyrpckit, including
  installation, mounting, Dishka, authentication, subscriptions and voice/media
  tests. Its exported-contract SDK checks already pass; see
  [RPC parity and migration limits](docs/rpc-parity.md).
- [ ] Complete Maximus's native Hermes runtime and browser E2E validation.
  Keep consumer-reported evidence separate from workspace verification; see
  [the adoption record](docs/compatibility.md#maximus-consumer-reported-adoption).
- [ ] Turn new contract/validation failures into minimal schema fixtures and
  regression cases before preparing another independent package release.

## Repository transition

- [ ] Add development-repository notices to the predecessor repositories and
  decide when their release pipelines should stop. Preserve existing repositories
  and tags; archival requires a separate explicit decision after migration.

## Deferred

- [ ] Revisit WebRTC's RPCKit signaling adapter, additional engines, ICE restart,
  forced-TURN CI and media-stall detection when a consumer needs them. See
  [decision 0005](docs/design-decisions/0005-webrtc-extension.md).
- [ ] Evaluate consumer-driven agent/browser examples, optional scaffolding and
  an installable constraints snapshot. Broader architecture ideas remain in
  [VISION.md](VISION.md); shared helpers need concrete reuse.
