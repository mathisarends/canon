# RPC successor parity and consumer checks

Verified locally on 2026-10-17. This records source and artifact checks for
`fastapi-rpckit` 0.1.0. The release is published and both SDKs also pass against
the installed PyPI package. Full application migration remains a separate step.

## Source inventory

The local `../pyrpckit` checkout is clean at
`853579eb08903bd95f8ce03f7608a3703ba40add` (pyrpckit 0.11.0), the same commit
imported into this workspace. All 79 tracked files under `rpckit/` and all 69
tracked test files are present in the successor under the new import namespace.

Comparing the imported implementation after reversing the namespace rename found
no missing runtime, schema, template, or test files. Differences consist of:

- The successor version, logger/context names, package imports, CLI attribution,
  installation messages, and formatting needed for the longer import namespace.
- Required FastAPI, four additional root exports (`FastApiSocket`, `RpcRoutes`,
  `create_router`, `serve_websocket`), and removal of optional-FastAPI error paths.
- Tests adjusted for required FastAPI and optional Dishka/OTel isolation. The
  inherited protocol/runtime regression cases remain intact.
- The subsequent Python generator fix described below, with a new regression test.

The JSON-RPC envelopes and IDs, method/event names, cancellation and subscription
controls, binary/raw framing, OpenRPC extensions, and generated client contracts
retain pyrpckit 0.11.0 behavior. Existing `x-rpckit-*` extensions, `.rpcgen`
manifests, and `rpckit.*` telemetry names remain intentional compatibility points.
There is no installed `rpckit` namespace shim.

## Functional coverage

The successor suite covers these inherited capabilities:

| Capability | Regression coverage |
| --- | --- |
| Methods, notifications, validation and typed errors | channel, dispatch, server, envelopes and error tests |
| FastAPI mounting, handshake authentication and rejections | FastAPI and expiry tests |
| Application/session/request dependencies | dependency and Dishka tests; composed stack test |
| Subscriptions, acknowledgement limits and cleanup | subscription, runtime and drain tests |
| Binary upload/download/duplex and raw sockets | stream/raw socket tests and generated roundtrips |
| Deadlines, cancellation, heartbeats, shutdown and credential refresh | dedicated server and Python/TypeScript SDK tests |
| OpenRPC, SDKs, tracing and middleware | schema, codegen, metadata, middleware and OTel tests |

Wheel checks independently exercise the CLI, JSON-RPC WebSocket roundtrips,
Python client roundtrips, TypeScript compilation and client drift. The composed
HTTP/SSE/RPC app also checks shared Dishka state and shutdown cleanup.

## Cara consumer contract

Selected consumer: `../cara/gateway`, observed at commit
`43178b931157caab9da59c1dad33cf8778af1470`. Its exported
`gateway/schema/gateway.openrpc.json` contains 15 methods; SHA-256:

```text
dee9bc02d414d978cfcdaf001b1ee1399c4dd9ed17b72773b3246e905391b004
```

The new wheel generates both SDKs from this contract. Python compilation,
package import, Ruff lint/format checks, TypeScript strict compilation and both
generator drift checks pass. Initially the Python generator produced overlong
enum defaults, discriminated event unions and route declarations. The generator
and templates now wrap those constructs; a synthetic contract regression covers
the same patterns. Names, validation and wire formats are unchanged.

Repeat against any exported consumer contract, after building the wheel and
installing the Streams member's TypeScript tooling:

```console
uv build --package fastapi-rpckit --out-dir dist/fastapi-rpckit
uv run --isolated --no-project --no-cache --with "dist/fastapi-rpckit/fastapi_rpckit-0.1.0-py3-none-any.whl[codegen]" --with ruff python -I scripts/check_rpc_consumer.py ../cara/gateway/schema/gateway.openrpc.json
```

`--no-cache` ensures a locally rebuilt development wheel with the same filename
does not reuse an older isolated installation. This is a contract/SDK check;
it does not start or migrate the Cara service.

Cara currently pins pyrpckit 0.8.0 and requires a separate application change:

1. Replace the dependency and `rpckit` imports with `fastapi-rpckit` and
   `fastapi_rpckit`. For FastAPI APIs use the root exports; use
   `fastapi_rpckit.integrations.dishka` for `DishkaResolver`.
2. In particular, replace `rpckit.fastapi` and `rpckit.dishka`; a mechanical
   namespace replacement would point to removed module paths.
3. Apply the predecessor's 0.9–0.11 changelog migrations, including request-ID,
   middleware and custom-transport changes wherever the application uses them.
4. Update the separate Canon `<0.5.0` pin if adopting Canon 0.5.0 as well.
5. Regenerate its committed SDKs, then run its actual authentication, mounting,
   Dishka, subscription, room/reverse-call and voice-media tests.

The older browser-provisioner consumer also has historical `pyrpckit` imports and
composition APIs; it needs its own version-specific migration. Neither external
repository was changed. Full consumer migration and live application tests remain
open; successful generation alone does not establish those claims.
