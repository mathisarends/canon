# Contracts and client generation

[Documentation](README.md) · [Project](../README.md)

## Export and generate

```sh
uv run fastapi-streams schema \
  --app examples.agent_runs:app --output tests/fixtures/agent_runs.openapi.json

uv run fastapi-streams generate \
  --schema tests/fixtures/agent_runs.openapi.json --language typescript --output frontend/generated

uv run fastapi-streams generate \
  --schema tests/fixtures/agent_runs.openapi.json --language python --output myapp/generated
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

Generated method documentation carries each operation's `summary`, `description`,
and `deprecated` marker alongside language-specific SDK behavior. Describe
replay, retention, and server job lifetime explicitly on your endpoint; the
generator does not infer these business guarantees. Python early exits should
use `contextlib.aclosing`; TypeScript `for await` cleanup closes its reader.

TypeScript has no runtime dependencies and uses Fetch-compatible APIs. The
example uses ES modules and is tested on Node 24. Generated Python packages
require Python 3.12+, `httpx>=0.28` and `pydantic>=2.11.2` (`uv add httpx pydantic`).

HTTPX is the default. To generate a Python client using HTTPX2 instead, opt in
when generating and checking it:

```sh
uv run fastapi-streams generate \
  --schema tests/fixtures/agent_runs.openapi.json --language python \
  --python-http-client httpx2 --output myapp/generated

uv run fastapi-streams check \
  --schema tests/fixtures/agent_runs.openapi.json --language python \
  --python-http-client httpx2 --output myapp/generated
```

Install `httpx2>=2.13.1,<3` and `pydantic>=2.11.2` in that consumer. The
generated package needs only the selected HTTP library; installing HTTPX2 does
not change an existing HTTPX client. The Python generator API accepts the same
choice as `generate_python(contract, http_client="httpx2")`. Pass the choice to
every `check` or `generate --check` call; omitting it checks HTTPX output.
`--python-http-client` requires `--language python`.

REST operations remain available in the contract for an existing SDK generator
such as Orval or HeyAPI. Keep REST and streaming SDKs in separate output
directories. Reusing external generated model imports is a future feature.

## Event discriminators

A Python default allows omitting a field when constructing a model. It does not
automatically make the field required in JSON Schema. The generator respects
`required` and warns with `OptionalDiscriminatorWarning` when a stream event
union uses an optional discriminator, including nested unions. An absent tag may
prevent variant selection; TypeScript's static types do not validate incoming JSON.

For **output-only** event models whose serializer always emits default fields,
configure the output schema to describe that behavior:

```python
from pydantic import BaseModel, ConfigDict


class StreamEvent(BaseModel):
    model_config = ConfigDict(
        json_schema_mode_override="serialization",
        json_schema_serialization_defaults_required=True,
    )
```

Inherit event variants from this model, or apply the configuration to an existing
output-only base. It marks all serialized default fields required, not only the
discriminator. Avoid applying it globally to shared request models: input and
output requiredness can differ. Alternatively, declare the tag without a default
and pass it explicitly. Regenerate the schema and clients after changing models.

Warnings are advisory and do not change fields or defaults. Python callers can
filter or promote this category using the standard `warnings` module; the category
is available from `fastapi_streams.codegen.diagnostics`.

## Check drift in CI

```sh
uv run fastapi-streams check \
  --app examples.agent_runs:app --schema tests/fixtures/agent_runs.openapi.json \
  --language typescript --output examples/agent_runs/generated

uv run fastapi-streams check \
  --app examples.agent_runs:app --schema tests/fixtures/agent_runs.openapi.json \
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
