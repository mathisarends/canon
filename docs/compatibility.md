# Compatibility

## Package versions

| Package | Published |
| --- | --- |
| `fastapi-canon` | 0.7.0 |
| `fastapi-streams` | 0.4.0 |
| `fastapi-rpckit` | 0.4.0 |
| `fastapi-webrtc` | 0.3.0 |

Published versions and assets are linked in the [README](../README.md#current-releases).
WebRTC 0.3.0 and Canon 0.7.0 were published on 2026-10-24. Follow the
[WebRTC migration notes](../packages/fastapi-webrtc/CHANGELOG.md#030---2026-10-24)
before upgrading custom engines. The [release record](releases.md#current-versions)
links the verified source and publication workflows.
Package metadata defines dependency ranges; the root `uv.lock` selects development
versions and does not establish support for every resolvable combination. Canon's
Streams and WebRTC extras pin the corresponding independently versioned package.
Canon core and each extension work independently.

Canon source 0.8.0 adds router policies and is not yet published. Its policy
contracts are exercised by the current/minimum installed-wheel smoke matrices;
the published-release verification record below still refers to Canon 0.7.0.

The current releases passed exact-source CI, current/minimum wheel
matrices and installed CLI/client checks before publication. Public installs cover
Canon core, each optional extra and both extras together. A fresh Windows/Python
3.14 installation also verified all four published packages together, including
HTTP/SSE/RPC/WebRTC routing and generated RPC SDK execution and compilation.

## Verification scope

CI runs package-specific lint/type checks, separate Python suites and generated
client drift/TypeScript tests on Linux with Python 3.12–3.14 and Windows with
Python 3.14. Linux/Python 3.14 also runs Chromium/aiortc browser tests and installed
artifact checks. See the [active CI workflow](../.github/workflows/ci.yml).

The installed-wheel matrix covers:

| Combination | What it establishes |
| --- | --- |
| Canon core | Import/runtime behavior with all extensions absent |
| Streams | Standalone SSE and CLI behavior |
| RPCKit | Standalone RPC, sockets and generated clients |
| Canon + Streams | Optional integration and HTTP/SSE contracts |
| Canon + RPCKit | Composition without Streams |
| Canon + Streams + RPCKit | Shared application state and Dishka cleanup |
| WebRTC core | Standalone declarations, contract/codegen and missing-engine diagnostics |
| WebRTC + aiortc | Optional engine installation |
| Canon + WebRTC | Admission contracts and optional integration |
| All four packages | Combined installation, routing and client generation |

Run `scripts/check_distributions.py` through the locked workspace environment for
current compatible dependencies. Add `--python 3.12 --dependencies minimum` for
the lowest jointly satisfiable direct runtime/extra bounds; transitive dependencies
resolve normally. Both modes build and install real artifacts in fresh environments
without local source overrides. Inventories are written to ignored
`dist/compatibility-{latest,minimum}.json`. This is a bounded smoke matrix, not
exhaustive testing of every compatible dependency combination.

The installed Streams CLI is also tested with no HTTP backend, HTTPX alone and
HTTPX2 alone. The installed WebRTC CLI regenerates the saved practice contract and
browser client, verifies provenance/drift and compiles the generated TypeScript.
See [contributing](contributing.md) for commands and [releases](releases.md) for
exact-source CI, dry-run and publication gates. Per-run results and artifact hashes
belong in Actions and GitHub Releases.

## External consumer limits

Cara's exported RPC contract can establish SDK generation/import/compilation and
drift compatibility. It cannot establish installation, mounting, authentication,
Dishka or media behavior of Cara's full application. Follow
[RPC parity and consumer checks](rpc-parity.md) for the installed-wheel command
and remaining migration scope.

For the preceding consumer integration releases, Maximus reported successful
native Linux Chromium/GStreamer integration and browser fallback tests. These
are consumer-reported results, not independent workspace deployment verification.
Deployed TURN/NAT, PostgreSQL concurrency and proxies still require
application-side validation.
