# Typed streams with canon errors

See [`docs/streams.md`](../../docs/streams.md) for the integration API and a
complete minimal application.

`CanonStreamRouter` combines `CanonRouter` and `fastapi_streams.StreamRouter`.
It inherits the native `stream()` decorator and routes registration through
canon's existing `api_route()` compiler. Shared and operation `raises=` use the
same registry membership checks and deduplication as REST routes. `Feature`
discovers the router's registry automatically; `Composition` installs the
handlers and OpenAPI compiler.

## Installation

For an installed canon checkout or release containing this integration:

```console
pip install "fastapi-canon[streams]"
```

The `streams` extra installs `fastapi-streams>=0.0.1,<0.1` from PyPI. The lower
bound is the tested release; the upper bound limits compatibility to the current
minor series. `uv.lock` fixes version 0.0.1 and package hashes for reproducible
repository checks. The extra selects Streams' higher requirements (FastAPI
>=0.143.3 and Pydantic >=2.11.2). The core runtime dependencies and normal
imports remain independent of Streams.

From this repository, start the executable example:

```console
uv run --extra streams --with uvicorn uvicorn examples.streams.app:app --reload
```

In another terminal:

```console
curl -N -H "Authorization: Bearer demo" http://localhost:8000/runs/1/events
curl -N -X POST -H "Authorization: Bearer demo" -H "Content-Type: application/json" -d '{"steps":2}' http://localhost:8000/runs/1/events
```

The example uses typed async generators for GET and POST, router-wide
authentication and local resource checks in dependencies. Omit authorization
for a 401 domain problem, use `Bearer forbidden` for a normalized 403
`HTTPException`, use run ID `0` for a 404 domain problem, or send an invalid run
ID/body for a normalized 422 validation problem. All use
`application/problem+json`. The successful response uses native SSE framing.

```python
from fastapi import Depends
from fastapi_canon.integrations.streams import CanonStreamRouter

router = CanonStreamRouter(
    prefix="/runs",
    error_registry=run_errors,
    raises=[authentication_required],
)


@router.stream(
    "/{run_id}/events",
    raises=[run_not_found],
    dependencies=[Depends(require_existing_run)],
)
async def events(run_id: int) -> AsyncIterator[RunEvent]:
    yield RunCompleted(run_id=run_id)
```

See [`app.py`](app.py) for complete definitions, authentication, POST, and
composition. Native stream restrictions apply: GET/POST only, concrete typed
generator events, and serialization options that preserve the event contract.
Let Streams infer the successful SSE response; no `CanonResponse.sse()` is
needed. Canon leaves the full `itemSchema` and `contentSchema` intact.

## Export and generate clients

Install the locked Streams codegen dependencies with the repository's group:

```console
uv sync --all-groups
uv run --group streams fastapi-streams schema --app examples.streams.app:app --output openapi.json
uv run --group streams fastapi-streams generate --schema openapi.json --language python --output generated/python
uv run --group streams fastapi-streams generate --schema openapi.json --language typescript --output generated/typescript
```

For an installed application, add `fastapi-streams[codegen]>=0.0.1,<0.1` and
lock it alongside your application dependencies. Both clients consume the same
exported OpenAPI 3.2 document, containing typed SSE events and canon problem schemas.

## Streaming boundary

Before the response starts, canon can return RFC 9457 HTTP problem responses.
Put authentication, authorization, and resource checks in dependencies.
**All generator body code, including code before the first `yield`, executes
after the response starts.** `raises=` documents HTTP error contracts; it does
not move generator execution or catch exceptions during a stream.

Business errors during an active stream require an application-specific error
event declared in your event union. Connection failures remain transport
errors. This integration adds neither `stream_raises` nor automatic conversion
of exceptions to events.

## Regression checks

`.github/workflows/streams.yml` tests Python 3.12 and 3.14 against both the locked
Streams release and its current `main` branch, on pushes, PRs, and weekly. It
checks error declarations, HTTP problems from dependencies, GET/POST streams,
the complete native SSE schema, and both client generators. The generated
Python client is also exercised against the combined ASGI application.
The package CI installs a clean wheel without Streams and tests the core
runtime separately. Locally:

```console
uv run --group streams pytest tests/integrations tests/test_optional_streams.py
```
