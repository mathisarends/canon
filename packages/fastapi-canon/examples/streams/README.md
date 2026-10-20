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

Published Canon 0.5.5 installs `fastapi-streams==0.4.0`. Both releases have verified
PyPI installs and matching GitHub Releases with original artifacts.
Upgrading requires an explicit
compatibility review and pin update. `uv.lock` records the workspace
combination for reproducible repository checks. The extra
selects Streams' higher requirements (FastAPI >=0.143.3 and Pydantic >=2.11.2).
The core runtime dependencies and normal
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
authentication and a Dishka-injected resource check in a dependency. The
`RunProvider` contributes a `Scope.REQUEST` service through `Feature.providers`;
`FromDishka[RunService]` injects that same service into the dependency and stream.
`Composition` installs the container and manages its lifecycle. Omit authorization
for a 401 domain problem, use `Bearer forbidden` for a normalized 403
`HTTPException`, use run ID `0` for a 404 domain problem, or send an invalid run
ID/body for a normalized 422 validation problem. All use
`application/problem+json`. The successful response uses native SSE framing.

```python
from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends
from fastapi_canon import HTTPMethod
from fastapi_canon.integrations.streams import CanonStreamRouter

router = CanonStreamRouter(
    prefix="/runs",
    error_registry=run_errors,
    raises=[authentication_required],
)


@router.stream(
    "/{run_id}/events",
    methods=[HTTPMethod.GET],
    raises=[run_not_found],
    dependencies=[Depends(require_existing_run)],
)
@inject
async def events(run_id: int, runs: FromDishka[RunService]) -> AsyncIterator[RunEvent]:
    async for event in runs.events(run_id):
        yield event
```

See [`app.py`](app.py) for complete definitions, authentication, POST, and
composition. Native stream restrictions apply: GET/POST only, concrete typed
generator events, and serialization options that preserve the event contract.
The POST declaration uses `methods=[HTTPMethod.POST]`, which selects only POST;
the list follows the native Streams API. `HTTPMethod` is exported by canon and
also works with REST `api_route()`. See the API guide for method selection and
Dishka decorator order.
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

An installed application can add `fastapi-streams[codegen]==0.4.0`
and lock it alongside its dependencies. Both clients consume the same
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

The [root CI workflow](../../../../.github/workflows/ci.yml) checks the locked workspace on Linux with
Python 3.12–3.14 and Windows with Python 3.14. Regression coverage includes
dependency problems, typed GET/POST streams, complete SSE schemas, both client
generators and Dishka lifetime/cleanup. Installed-wheel checks also exercise
Canon with Streams absent. Run the focused suite from the repository root:

```console
uv run --locked --directory packages/fastapi-canon python -m pytest tests/integrations tests/test_optional_streams.py
```
