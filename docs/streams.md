# fastapi-streams integration API

Install the optional integration:

```console
pip install "fastapi-canon[streams]"
```

Import the router explicitly:

```python
from fastapi_canon.integrations.streams import CanonStreamRouter
```

The extra supports `fastapi-streams>=0.0.1,<0.1`; `uv.lock` records the tested
release and hashes. Streams requires FastAPI >=0.143.3 and Pydantic >=2.11.2.
Installing and importing canon without the extra continues to work.

## Complete integration example

Save this as `app.py` and run `uvicorn app:app` with Uvicorn installed:

```python
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI, Header
from pydantic import BaseModel

from fastapi_canon import Composition, Error, ErrorRegistry, Feature
from fastapi_canon.integrations.streams import CanonStreamRouter


class AuthenticationRequired(Exception):
    pass


class RunNotFound(Exception):
    pass


class RunEvent(BaseModel):
    run_id: str
    message: str


authentication_required = Error(
    AuthenticationRequired,
    status=401,
    code="authentication_required",
    title="Authentication required",
)
run_not_found = Error(
    RunNotFound, status=404, code="run_not_found", title="Run not found"
)
run_errors = ErrorRegistry(
    name="runs",
    errors=[authentication_required, run_not_found],
    type_base="https://api.example.com/problems",
)


async def require_authentication(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    if authorization != "Bearer demo":
        raise AuthenticationRequired


async def require_existing_run(run_id: str) -> None:
    if run_id != "demo":
        raise RunNotFound


router = CanonStreamRouter(
    prefix="/runs",
    error_registry=run_errors,
    raises=[authentication_required],
    dependencies=[Depends(require_authentication)],
)


@router.stream(
    "/{run_id}/events",
    raises=[run_not_found],
    dependencies=[Depends(require_existing_run)],
    operation_id="run_events",
)
async def events(run_id: str) -> AsyncIterator[RunEvent]:
    yield RunEvent(run_id=run_id, message="Started")
    yield RunEvent(run_id=run_id, message="Completed")


feature = Feature(name="runs", routers=[router])
composition = Composition(feature)
app = composition.apply(FastAPI())
composition.validate(app)
```

Request `GET /runs/demo/events` with `Authorization: Bearer demo` to receive SSE.
Omit the header for a 401 problem, or request another run ID for a 404 problem.
`Feature` automatically collects the registry from the router; declaring
`errors=run_errors` on the feature is optional. `Composition` installs the
runtime handlers and OpenAPI compiler together.

## Router and operation options

`CanonStreamRouter` inherits `CanonRouter` and `StreamRouter`. It combines their
existing APIs without replacing registration, validation, or serialization.

| API | Behavior |
| --- | --- |
| `CanonStreamRouter(error_registry=registry, raises=[...], **options)` | The registry contains available errors. Router-level `raises` applies to operations declared on this router. Standard FastAPI router options pass through. |
| `router.stream(path, raises=[...], methods=None, **options)` | Local errors extend shared errors. Defaults to GET; use `methods=["POST"]` for a body-driven stream. FastAPI dependencies, tags, operation IDs, and manual responses pass through. |
| `router.get(...)`, `router.post(...)`, `router.api_route(...)` | Normal canon REST declarations remain available on the same router. |

Every declared error must be an `Error` instance in that router's registry.
Nonempty `raises` requires a registry. Duplicate instances, including errors
declared at both levels, appear once. Distinct errors with the same HTTP status
use canon's discriminated `oneOf` problem schema. Invalid declarations raise
`ErrorConfigurationError` during router construction or endpoint registration.
As with `CanonRouter`, shared `raises` does not propagate to included child routers.

Use an annotated generator (`AsyncIterator[RunEvent]`, or `Iterator[RunEvent]`
for synchronous endpoints). Streams infers its successful SSE response and
rejects incompatible methods, response models, and serialization options. No
`CanonResponse.sse()` declaration is needed. Typed POST bodies and a
discriminated event union are shown in the executable
[`examples/streams/app.py`](../examples/streams/app.py).

To document normalized `HTTPException` statuses, use canon's existing
`responses=run_errors.responses(http_statuses=[403])` router/operation option.
Request validation errors are normalized and documented by `Composition` by
default. For manual app assembly, include the router and call
`run_errors.install(app)` before generating OpenAPI.

## Export and client generation

Canon preserves Streams' complete native `itemSchema` and JSON `contentSchema`,
including referenced models and event discriminators. The exported contract
also contains the declared `application/problem+json` responses. From this repo:

```console
uv sync --all-groups
uv run --group streams fastapi-streams schema --app examples.streams.app:app --output openapi.json
uv run --group streams fastapi-streams generate --schema openapi.json --language python --output generated/python
uv run --group streams fastapi-streams generate --schema openapi.json --language typescript --output generated/typescript
```

For another application, install `fastapi-streams[codegen]>=0.0.1,<0.1` and use
your app's module path instead. Both clients consume the same OpenAPI 3.2 contract.

## Streaming boundary

- **Before response start:** authentication, authorization, and resource checks
  in dependencies can raise domain exceptions. Canon returns RFC 9457 HTTP
  problems, including normalized HTTP and request validation errors.
- **During streaming:** every generator statement, even before its first
  `yield`, executes after response start. Business errors need an explicit
  application error event in the event model/union.
- **Connection failures:** disconnects remain transport errors.

`raises=` documents HTTP contracts. It does not move generator execution, catch
stream exceptions, or convert them to events. There is no `stream_raises` API.

## Compatibility regression checks

The [Streams CI workflow](../.github/workflows/streams.yml) runs the full suite
on Python 3.12 and 3.14 against the locked release and current upstream `main`,
on pushes, pull requests, and weekly. Regression tests cover dependency errors,
validation, typed GET/POST streams, complete SSE schemas, and both client
generators. The generated Python client also makes successful and failing
requests against the combined app. Separate clean-wheel checks exercise canon
without Streams installed.

See the [runnable example guide](../examples/streams/README.md) for curl commands
and local regression test commands.
