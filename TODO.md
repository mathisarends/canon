# Next work

Updated: 2026-10-20. Keep this list limited to open work. Published versions are
listed in the [README](README.md#current-releases); completed work and evidence
belong in [migration](docs/migration.md), [releases](docs/releases.md) and
[compatibility](docs/compatibility.md).

## Current priority

- [ ] Finish review and merge [WebRTC PR #7](https://github.com/mathisarends/canon/pull/7)
  after CI passes on the final commit. The review fixes and Canon/Dishka lifecycle
  coverage are implemented; WebRTC 0.1.0 remains unreleased.
- [ ] When release preparation is requested, select independent versions for
  WebRTC, RPCkit's merged changes and the Canon lifecycle fix. RPCkit's source
  remains 0.2.0 with changes documented under unreleased 0.3.0; PRs #4, #5 and
  [#6](https://github.com/mathisarends/canon/pull/6) are merged.
- [ ] Before WebRTC's first publication, confirm its PyPI Trusted Publisher and
  release-environment setup, then pass final-source CI and a release dry run.
  Follow [the release procedure](docs/releases.md); publication needs explicit
  authorization and complete PyPI/tag/GitHub Release verification.

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
