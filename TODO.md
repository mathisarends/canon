# Next work

Updated: 2026-10-20. Keep this list limited to open work. Published versions are
listed in the [README](README.md#current-releases); completed work and evidence
belong in [migration](docs/migration.md), [releases](docs/releases.md) and
[compatibility](docs/compatibility.md).

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
