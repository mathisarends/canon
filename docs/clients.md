# TypeScript and Python clients

[Documentation](README.md) · [Project](../README.md)

## Named values and typed iteration

Discriminated unions produce an enum named after the union and discriminator:
`RunEvent` + `type` becomes `RunEventType`. String enums and literal model fields
also get named values. Python emits `StrEnum`; TypeScript emits an `as const`
object plus a union type. Both retain exhaustive discriminator narrowing.
Parameters use camelCase in TypeScript and snake_case in Python; wire aliases
are preserved.

```typescript
import { createClient, RunEventType } from "./generated/index.js";

const client = createClient({
  baseUrl: "http://localhost:8000",
  headers: { Authorization: "Bearer demo-token" },
});
const controller = new AbortController();
for await (const event of client.agentRuns.streamRunEvents(
  { runId: "demo" }, { signal: controller.signal },
)) {
  switch (event.type) {
    case RunEventType.RUN_STARTED: console.log(event.run_id); break;
    case RunEventType.TOKEN_DELTA: console.log(event.text); break;
    case RunEventType.RUN_COMPLETED: console.log(event.run_id); break;
    case RunEventType.RUN_FAILED: console.error(event.message); break;
    default: {
      const exhaustive: never = event;
      throw new Error(`Unexpected event: ${exhaustive}`);
    }
  }
}
```

```python
from myapp.generated import Client, RunEventType

async with Client(
    "http://localhost:8000", headers={"Authorization": "Bearer demo-token"}
) as client:
    async for event in client.agent_runs.stream_run_events(run_id="demo"):
        match event.type:
            case RunEventType.TOKEN_DELTA:
                print(event.text, end="", flush=True)
            case RunEventType.RUN_COMPLETED:
                print(event.run_id)
```

For POST, TypeScript accepts `streamPrompt({ runId, body: { prompt: "Hello" } })`.
Python accepts `stream_prompt(run_id="demo", body=RunRequest(prompt="Hello"))`;
import `RunRequest` from the generated `models` module.

## Python HTTP library

Generated Python clients use HTTPX by default. Generate with
`--python-http-client httpx2` to opt in to HTTPX2 and install
`httpx2>=2.13.1,<3` alongside Pydantic in the consuming project. Client methods,
event models and SDK errors stay the same. See the [generator options](codegen.md).

When injecting a client, use the library selected at generation time:

```python
import httpx2
from myapp.generated import Client

async with httpx2.AsyncClient(timeout=30) as http:
    async with Client("http://localhost:8000", http_client=http) as client:
        async for event in client.agent_runs.stream_run_events(run_id="demo"):
            print(event)
```

Use `httpx.AsyncClient` for the default generated client. Each generated variant
uses its library's native client, response and exception types; Pyright rejects
injection from the other library. HTTPX2 clients follow HTTPX2's native transport
and TLS defaults; see its [migration guide](https://pydantic.dev/docs/httpx2/get-started/migration/).

## Cancellation and errors

TypeScript accepts a custom `fetch`, base URL, client/request headers,
credentials and an `AbortSignal`. Breaking `for await` cancels the reader and
aborts the request. Parsing handles arbitrary byte boundaries, fragmented UTF-8,
LF/CRLF/CR, multiline data, comments, heartbeats and final EOF events.

Python accepts an injected async HTTP client and per-call `RequestOptions`.
Injected clients stay caller-owned. Cancelling a consuming task closes its
response.

Requests inherit the injected client's timeout unless explicitly overridden
with `RequestOptions(timeout=seconds)`. `RequestOptions(timeout=None)` disables
timeouts for that request. The SDK-owned client defaults to no timeout for streams.

Use `aclosing` for deterministic cleanup when exiting early:

```python
from contextlib import aclosing

async with aclosing(client.agent_runs.stream_run_events(run_id="demo")) as events:
    async for event in events:
        print(event)
        break
```

Both SDKs expose `HttpError` (status, response and available JSON/text details),
`StreamParseError` (invalid event data) and `TransportError` (network/protocol
failure). HTTP diagnostics are bounded to 64 KiB. Python validates events with
Pydantic; TypeScript provides static types and JSON decoding, with no runtime
schema validator. Cancellation propagates normally; application error events
remain ordinary members of the user-defined union.

Python uses `None` for omitted optional fields; `model_fields_set` distinguishes
absence from explicit null. Explicit null is rejected for fields that may only
be omitted. Requests exclude unset fields and serialize using wire aliases.
