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
- [ ] Validate Maximus against deployed TURN/NAT, PostgreSQL concurrency and
  proxies. Native Linux Hermes/browser E2E is now reported by the consumer;
  keep it separate from workspace verification. See
  [the adoption record](docs/compatibility.md#maximus-consumer-reported-adoption).
- [ ] Turn new contract/validation failures into minimal schema fixtures and
  regression cases before preparing another independent package release.

## Release preparation

- [ ] Finalize changelog dates and repeat exact-source CI before an explicitly
  authorized publication of WebRTC 0.2.0, RPCkit 0.4.0 and Canon 0.6.0. Publish
  WebRTC before Canon; verify public installs, tags, GitHub Releases and attached
  artifacts. Prepared sources and dry runs are not publication; see
  [release preparation](docs/releases.md#consumer-integration-preparation-2026-10-20).

## Repository transition

- [ ] Add development-repository notices to the predecessor repositories and
  decide when their release pipelines should stop. Preserve existing repositories
  and tags; archival requires a separate explicit decision after migration.

## Deferred

- [ ] Revisit WebRTC's RPCKit signaling adapter, additional engines, ICE restart,
  forced-TURN CI, native engine adapters and a maintained CDP binding when a
  consumer needs them. Media health and a remote lease example are implemented
  in the prepared source; see
  [decision 0006](docs/design-decisions/0006-consumer-integration.md) and
  [decision 0005](docs/design-decisions/0005-webrtc-extension.md).
- [ ] Evaluate consumer-driven agent/browser examples, optional scaffolding and
  an installable constraints snapshot. Broader architecture ideas remain in
  [VISION.md](VISION.md); shared helpers need concrete reuse.
