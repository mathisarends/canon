# Development

[Documentation](README.md) · [Project](../README.md)

## Run the checks

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

## Supported scope and roadmap

GET/POST JSON SSE data; scalar path and header parameters; scalar/array query parameters;
JSON bodies; local component references; nested objects, maps, arrays, string
enums and discriminated unions. Query form arrays support both `explode` values.
Python `allOf` supports compatible object intersections. TypeScript does not
express validation constraints such as numeric ranges as refinement types.

Header arrays (Fetch combines repeated headers), external references, cookies,
deepObject/matrix/label styles, multipart bodies,
tuple schemas and object/array enum values are rejected. No REST SDK replacement,
WebSockets, JSON-RPC, persistence, automatic reconnect or replay.

Next: NDJSON, then explicit event IDs, Last-Event-ID and opt-in reconnect/replay
policies. Both shipped generators already share a transport-independent HTTP IR.
