# 004 — Preserve explicit additionalProperties policies in Python models

Status: Open
Priority: P2
Scope: Shared object IR, Python model config, schema validation regressions
Integration: After 002; before 005 and 006 to coordinate shared IR edits.

## Problem

An object schema with `additionalProperties: false` generates a Python model
with `ConfigDict(populate_by_name=True)`, whose default extra-field behavior is
to ignore unknown keys. Forbidden fields are silently discarded instead of
causing validation failure.

This affects ordinary source models configured with `extra="forbid"`, as well
as custom schemas. Requests can be silently changed before sending, and invalid
stream events are accepted despite the explicit contract restriction.

## Relevant code

- `fastapi_streams/codegen/ir.py`: `Object`, `_Types.parse()` object handling
  (review baseline: lines 415–435).
- `fastapi_streams/codegen/python.py`: `_Models.render()` model configuration
  (review baseline: lines 278–293), plus `_object()` intersection handling.
- `tests/codegen/test_schema_matrix.py` and `test_intersections.py`.

## Reproduction

Generate a Python model for:

```json
{
  "type": "object",
  "properties": {"name": {"type": "string"}},
  "required": ["name"],
  "additionalProperties": false
}
```

Use `schema_contract()`, `generate_python()`, and `load_models()` from the
existing test helpers. Then:

```python
parsed = TypeAdapter(models.EventsEvent).validate_python(
    {"name": "a", "unexpected": 123}
)
```

Observed result: validation succeeds with `EventsEvent(name='a')`; the extra
property has disappeared. The expected result is a validation error.

## Proposed implementation

Preserve enough information in the shared IR to distinguish explicit forbidden
extras, unrestricted extras, typed extras, and the current treatment of omitted
`additionalProperties`. The existing representation conflates an explicit
prohibition with other cases; globally replacing every default with
`extra="forbid"` would introduce unrelated behavior changes.

Emit `extra="forbid"` where the contract explicitly requires it. Retain typed
extra validation and existing default-model behavior. Review `allOf` merging:
merging models must not accidentally turn a closed schema into an open one.
Reject intersections that cannot be represented faithfully rather than silently
weakening them.

## Acceptance criteria

- The reproduced payload raises `ValidationError` against the generated model.
- A real source `BaseModel` with `ConfigDict(extra="forbid")` preserves that
  behavior through export and generation.
- When that model is an SSE event, a forbidden extra property becomes
  `StreamParseError` through the generated Python transport.
- Request-body serialization does not silently discard explicitly forbidden
  extras during validation.
- Explicit `additionalProperties: true`, typed extras, and schemas omitting the
  keyword have separate regression coverage.
- Compatible existing intersections still work; unsupported closed-object
  intersections fail explicitly rather than losing their restrictions.
- No TypeScript runtime schema validator is introduced; that remains outside
  the documented v0.0.1 scope.

## Validation

Run schema-matrix, intersection, Python client, and typing tests; then the Python
suite, TypeScript checks if shared output changes, and artifact regeneration/
drift checks. Exercise runtime validation with both Python HTTP backends.
