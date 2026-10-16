# Contracts and client generation

[Documentation](README.md) · [Project](../README.md)

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

## Check drift in CI

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
