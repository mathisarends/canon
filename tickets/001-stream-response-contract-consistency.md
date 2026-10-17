# 001 — Keep stream serialization and generated contracts consistent

Status: Complete
Priority: P1
Scope: StreamRouter registration, contract export, regression tests

## Problem

`StreamRouter.stream()` forwards response serialization options to FastAPI, but
the exported event schema still describes the original model. Some accepted
options therefore make the actual SSE payload incompatible with both SDKs.
The generated Python SDK rejects a successful server event; the TypeScript SDK
claims fields exist that are absent at runtime.

Confirmed cases:

1. `response_model_exclude={"secret"}` removes a required property from the wire,
   while the exported schema and generated Python model still require it.
2. `response_model_by_alias=False` emits a model's Python field name, while the
   exported schema describes its serialization alias.

## Relevant code

- `fastapi_streams/router.py`: `StreamRouter.stream()`, particularly the option
  validation and `self.api_route(..., **options)` call (review baseline: lines
  33–58).
- `fastapi_streams/codegen/openapi.py`: `export_schema()` copies native OpenAPI.
- `tests/router/test_router.py` and contract/client integration tests.

## Reproduction

Create a finite stream returning this model:

```python
class Event(BaseModel):
    public: str
    secret: str


@router.stream("/events", operation_id="events", response_model_exclude={"secret"})
async def events() -> AsyncIterator[Event]:
    yield Event(public="ok", secret="hidden")
```

Export the app with `export_schema()`, build the IR, and generate Python models.
Request the route using `TestClient`. The response contains
`data: {"public":"ok"}`. Validating that data against the generated `Event`
raises a missing-field error for `secret`; the SDK transport exposes this as
`StreamParseError`.

For the alias case, use `value: str = Field(alias="external-value")` and
`response_model_by_alias=False`. The wire contains `{"value":"ok"}`, but the
generated model requires `external-value` (its Python name is `external_value`).
This also fails validation. Both cases were reproduced against a real FastAPI
application using `TestClient`.

## Proposed implementation

For v0.0.1, prefer a clear registration-time error for options whose effect is
not represented by the exported schema. Do not attempt a broad schema-rewriting
system unless it can faithfully preserve request/response model differences.

Audit `response_model_include`, `response_model_exclude`,
`response_model_by_alias`, `response_model_exclude_none`,
`response_model_exclude_unset`, and `response_model_exclude_defaults`. Distinguish
safe default/no-op values from configurations that can change the contract.
For example, excluding `None` can remove a required nullable property.

Keep ordinary route options such as dependencies, tags, success status codes,
and response headers working. Document any unsupported serialization options in
the router docstring and the appropriate user guide.

## Acceptance criteria

- Each confirmed configuration either fails clearly at route registration or
  exports a schema that exactly matches the emitted event and produces working
  Python and TypeScript clients. It must not succeed silently and later fail
  while consuming a valid server response.
- Cover both the required-field exclusion and alias examples with regressions.
- Cover a required nullable field together with `response_model_exclude_none`.
- Default serialization, ordinary aliases, GET/POST registration, and existing
  dependency/status-code behavior remain compatible.
- Tests verify registration/contract/wire behavior rather than merely comparing
  generated source strings.

## Validation

Implemented registration-time rejection of contract-changing include/exclude,
alias and omission settings; documented the supported no-op values. Regressions
cover all six options and validate real GET/POST SSE payloads (including aliases
and required nulls) against freshly generated Python models. No schema rewriting
is attempted; use a dedicated event model for a different payload shape.

Validation: the seven new rejection cases failed before the fix;
`uv run pytest -q` passed **134 tests** after it.
`uv run python scripts/codegen.py --check` passed with no artifact changes.

Run focused router and contract tests, the new generated-client regressions,
the complete Python suite, and generated-artifact drift checks. If schemas or
generated output change, regenerate them through the existing generators.
