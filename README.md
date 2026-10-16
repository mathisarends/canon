# fastapi-streams

**Define events once in Python. Get a typed FastAPI stream, an OpenAPI contract,
and TypeScript and Python clients with named event values.**

```typescript
import { createClient, RunEventType } from "./generated/index.js";

const client = createClient({ baseUrl: "http://localhost:8000" });
for await (const event of client.agentRuns.streamRunEvents({ runId: "demo" })) {
  switch (event.type) {
    case RunEventType.TOKEN_DELTA:
      console.log(event.text); // narrowed to TokenDelta
      break;
  }
}
```

Native FastAPI dependencies, security, validation, middleware and nested routers
keep working. The server uses FastAPI's `EventSourceResponse`; generated clients
handle incremental SSE parsing and cleanup. Python 3.12+, FastAPI 0.143.3+,
Pydantic v2. MIT licensed.

## Run the complete example

```sh
git clone https://github.com/mathisarends/fastapi-streams.git
cd fastapi-streams
uv sync --all-extras
npm ci
uv run python scripts/codegen.py
uv run uvicorn examples.agent_runs:app --reload
```

In another terminal:

```sh
# TypeScript
npx tsc -p tests/typescript/tsconfig.json
node tests/typescript/dist/examples/agent_runs/consume.js

# Python
uv run python -m examples.agent_runs.consume
```

Both consume streamed tokens, including Unicode. The example also has a POST
stream authenticated with `Authorization: Bearer demo-token`, and a normal
`/health` REST endpoint. The example token is for local demonstration.

## Define a stream

The server package needs only FastAPI and Pydantic. Install the optional
`fastapi-streams[codegen]` extra where you generate contracts and SDKs. From this
checkout use `uv sync --all-extras`; `uv build` produces an installable wheel and
sdist. Once published, use `uv add 'fastapi-streams[codegen]'` in another project.

```python
from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field
from fastapi_streams import StreamRouter


class TokenDelta(BaseModel):
    type: Literal["token.delta"]
    text: str


class RunCompleted(BaseModel):
    type: Literal["run.completed"]
    run_id: str


type RunEvent = Annotated[TokenDelta | RunCompleted, Field(discriminator="type")]

router = StreamRouter(prefix="/runs", tags=["agentRuns"])


@router.stream("/{run_id}/events", operation_id="stream_run_events")
async def stream_run_events(run_id: str) -> AsyncIterator[RunEvent]:
    yield TokenDelta(type="token.delta", text="Hello")
    yield RunCompleted(type="run.completed", run_id=run_id)


app = FastAPI()
app.include_router(router, prefix="/v1")
```

`StreamRouter` extends `APIRouter`. `stream()` defaults to GET and SSE. Pass
`methods=["POST"]` for JSON request bodies. Options such as `dependencies`,
`responses`, `tags`, `operation_id`, `status_code` and serialization options
pass through to FastAPI. Stable operation IDs make the generated API stable.
The original function and signature are registered directly.

Async generators support `AsyncIterator[T]`, `AsyncIterable[T]` and
`AsyncGenerator[T, None]`; sync generators support `Iterator[T]`, `Iterable[T]`
and `Generator[T, None, None]`. Missing annotations, `Any`, bare containers,
coroutines returning iterators and untyped `ServerSentEvent` envelopes are
rejected. Yield application data; FastAPI owns framing, heartbeats and ASGI.

Put authentication and other HTTP preconditions in dependencies. A generator
body executes after the response starts, so exceptions inside it cannot change
the HTTP status. Represent application failures in your own event union when
needed, as the example's `RunFailed` does.

## Export and generate

```sh
uv run fastapi-streams schema \
  --app examples.agent_runs:app --output schema/openapi.json

uv run fastapi-streams generate \
  --schema schema/openapi.json --language typescript --output frontend/generated

uv run fastapi-streams generate \
  --schema schema/openapi.json --language python --output myapp/generated
```

No running server is needed. Export imports the application. The codegen extra
adds Jinja and JSON Schema validation; importing the server package needs neither.

The exporter copies native FastAPI output, promotes compatible 3.1 output to
OpenAPI 3.2.0, updates the declared OAS dialect when necessary, and validates the
official bundled OpenAPI structural schema, Draft 2020-12 Schema Objects and
local references. Incompatible contracts fail explicitly. The application's
cached document and ordinary REST endpoints remain intact.

The generator extracts application data from
`itemSchema.properties.data.contentSchema`. Only stream operations and models
reachable from their parameters, bodies, events and error responses are emitted.
Operations use the first tag as their group, defaulting to `streams`.

TypeScript has no runtime dependencies and uses Fetch-compatible APIs. The
example uses ES modules and is tested on Node 24. Generated Python packages
require Python 3.12+, `httpx>=0.28` and `pydantic>=2.11` (`uv add httpx pydantic`).

REST operations remain available in the contract for an existing SDK generator
such as Orval or HeyAPI. Keep REST and streaming SDKs in separate output
directories. Reusing external generated model imports is a future feature.

## Similar clients, named event values

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

## Cancellation and errors

TypeScript accepts a custom `fetch`, base URL, client/request headers,
credentials and an `AbortSignal`. Breaking `for await` cancels the reader and
aborts the request. Parsing handles arbitrary byte boundaries, fragmented UTF-8,
LF/CRLF/CR, multiline data, comments, heartbeats and final EOF events.

Python accepts an injected `httpx.AsyncClient` and per-call `RequestOptions`.
Injected clients stay caller-owned. Cancelling a consuming task closes its
response. Use `aclosing` for deterministic cleanup when exiting early:

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

## Detect drift in CI

```sh
uv run fastapi-streams check \
  --app examples.agent_runs:app --schema schema/openapi.json \
  --language typescript --output examples/agent_runs/generated

uv run fastapi-streams check \
  --app examples.agent_runs:app --schema schema/openapi.json \
  --language python --output examples/agent_runs/generated_python
```

`check` imports the app, compares its contract, validates the stored schema and
compares generated files without writing. Omit `--app` for a contract supplied
by another service. `schema --check` and `generate --check` are also supported.
Exit codes: **0** current, **1** drift, **2** invalid input.

Generation is deterministic. A manifest tracks owned files and cleans up stale
generated files without deleting neighboring handwritten files. Use a dedicated
output directory for each language. Unsafe paths and generated-name collisions
fail explicitly.

## Development

```sh
uv sync --all-extras
npm ci
uv run ruff check .
uv run ruff format --check .
uv run pyright
npm run typecheck
npm test
uv run pytest -q
uv run python scripts/codegen.py --check
uv build
```

Run `uv run python scripts/codegen.py` to regenerate all committed examples and
test fixtures. The tests cover real FastAPI-to-Node and FastAPI-to-Python HTTP
requests, strict narrowing, recursive models, authentication, disconnect
cleanup, fragmented parsing, cancellation and drift detection. Install Node
dependencies before pytest to enable its TypeScript acceptance test. CI does
this and checks Python 3.12, 3.13 and 3.14. Generated Python is checked by Pyright
and behavior tests; its generator owns formatting.

## v0.1 scope

GET/POST JSON SSE data; scalar paths; scalar/array query and header parameters;
JSON bodies; local component references; nested objects, maps, arrays, string
enums and discriminated unions. Query form arrays support both `explode` values.
Python `allOf` supports compatible object intersections. TypeScript does not
express validation constraints such as numeric ranges as refinement types.

External references, cookies, deepObject/matrix/label styles, multipart bodies,
tuple schemas and object/array enum values are rejected. No REST SDK replacement,
WebSockets, JSON-RPC, persistence, automatic reconnect or replay.

Next: NDJSON, then explicit event IDs, Last-Event-ID and opt-in reconnect/replay
policies. Both shipped generators already share a transport-independent HTTP IR.
