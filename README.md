# fastapi-streams

[![CI](https://github.com/mathisarends/fastapi-streams/actions/workflows/ci.yml/badge.svg)](https://github.com/mathisarends/fastapi-streams/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](pyproject.toml)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Define typed HTTP streams in FastAPI. Generate TypeScript and Python clients
from the same OpenAPI contract.**

Keep your Pydantic models, FastAPI dependencies and routing. Add
`@router.stream()`, export OpenAPI 3.2, and consume events through typed async
iteration. The generated SDKs handle SSE parsing and cleanup.

## Named events in both clients

Discriminated unions become named event values: an `as const` object in
TypeScript and a `StrEnum` in Python. Both retain type narrowing.

```typescript
import { createClient, RunEventType } from "./generated/index.js";

const client = createClient({ baseUrl: "http://localhost:8000" });

for await (const event of client.agentRuns.streamRunEvents({ runId: "demo" })) {
  switch (event.type) {
    case RunEventType.TOKEN_DELTA:
      console.log(event.text);
      break;
    case RunEventType.RUN_COMPLETED:
      console.log(event.run_id);
      break;
  }
}
```

```python
from myapp.generated import Client, RunEventType

async with Client("http://localhost:8000") as client:
    async for event in client.agent_runs.stream_run_events(run_id="demo"):
        match event.type:
            case RunEventType.TOKEN_DELTA:
                print(event.text, end="", flush=True)
            case RunEventType.RUN_COMPLETED:
                print(event.run_id)
```

## Quickstart

Requires Python 3.12+ and uv. The TypeScript example also needs Node.js and npm.

```sh
git clone https://github.com/mathisarends/fastapi-streams.git
cd fastapi-streams
uv sync --all-extras
npm ci
uv run uvicorn examples.agent_runs:app --reload
```

In another terminal, run either generated client:

```sh
# TypeScript
npx tsc -p tests/typescript/tsconfig.json
node tests/typescript/dist/examples/agent_runs/consume.js

# Python
uv run python -m examples.agent_runs.consume
```

The repository includes the exported contract, both generated SDKs, and a
runnable example with GET and authenticated POST streams.
[Define your own endpoint →](docs/quickstart.md#define-your-own-stream)

## Generate and check

Code generation is available through the optional `fastapi-streams[codegen]`
extra, included in the checkout setup above. It needs no running server.

```sh
uv run fastapi-streams schema --app examples.agent_runs:app --output schema/openapi.json
uv run fastapi-streams generate --schema schema/openapi.json --language typescript --output frontend/generated
uv run fastapi-streams generate --schema schema/openapi.json --language python --output myapp/generated
```

Use `fastapi-streams check --app ... --schema ... --language ... --output ...`
to detect contract and client drift without writing. For this repository:

```sh
uv run python scripts/codegen.py --check
```

## Documentation

| Guide | Topics |
| --- | --- |
| [Quickstart](docs/quickstart.md) | Installation, event models, and native FastAPI integration. |
| [Contracts and codegen](docs/codegen.md) | OpenAPI 3.2, both generators, and CI drift checks. |
| [Client usage](docs/clients.md) | Enums, authentication, cancellation, and errors. |
| [Development](docs/development.md) | Tests, quality checks, supported scope, and roadmap. |
| [Architecture](docs/architecture.md) | Native SSE, shared HTTP IR, templates, and transports. |

## Scope

v0.1 supports GET/POST JSON SSE streams, nested Pydantic schemas, discriminated
unions, Fetch and HTTPX clients. Normal REST endpoints remain in the contract
for your existing REST SDK. Automatic reconnection, replay, event IDs and
additional stream formats are deferred. See the [supported scope](docs/development.md#supported-scope-and-roadmap).

FastAPI 0.143.3+ · Pydantic v2 · [MIT](LICENSE)
