# Next work

## External consumers

- [ ] Complete Cara Gateway's application migration from pyrpckit, including
  mounting, Dishka, authentication, subscriptions and voice/media tests. Exported
  contract checks are covered in [RPC parity](docs/rpc-parity.md).
- [ ] Validate deployed Maximus TURN/NAT, PostgreSQL concurrency and proxies.
  Native Linux runtime and browser tests are consumer-reported evidence.
- [ ] Reduce new consumer contract failures to regression fixtures.

## Releases

- [ ] After the repository cleanup, finalize changelog dates and repeat exact-source
  CI and release dry runs for WebRTC 0.2.0, RPCkit 0.4.0 and Canon 0.6.0. Publish
  only when explicitly authorized, with WebRTC before Canon. Follow
  [the release process](docs/releases.md).

## Repository transition

- [ ] Add development-repository notices to predecessor repositories and decide
  when their release pipelines should stop. Archive only after completed
  migrations and a separate explicit decision.

## Deferred

- [ ] Revisit RPCKit signaling for WebRTC, additional native engines, ICE restart,
  forced-TURN CI and a maintained CDP binding when concrete consumers need them.
- [ ] Evaluate agent/browser examples, optional scaffolding and an installable
  constraints snapshot. Extract shared helpers only for demonstrated reuse.
