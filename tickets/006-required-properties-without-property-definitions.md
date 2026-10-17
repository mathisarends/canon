# 006 — Retain required keys that are not listed in properties

Status: Complete
Priority: P2
Scope: Shared object IR, both generators, schema matrix
Integration: After 004 and 005 to reuse their object-policy/reference changes.

## Problem

Object parsing only creates fields by iterating over `properties`. Names that
appear exclusively in `required` are lost. A schema requiring a key can become
an unrestricted map, allowing `{}` in both the Python SDK and TypeScript types.

This is most relevant to custom or externally supplied contracts. The current
contract validator and code generators accept the schema without warning.

## Relevant code

- `fastapi_streams/codegen/ir.py`: `_Types.parse()` object branch, particularly
  `for name, value in sorted(properties.items())` (review baseline: lines 415–435).
- `fastapi_streams/codegen/python.py`: `_Models.render()` emits `dict[str, ...]`
  when an object has no explicit fields and permits additional properties.
- `fastapi_streams/codegen/typescript.py`: `render_type()` object/index handling.
- `tests/codegen/test_schema_matrix.py`.

## Reproduction

Generate clients for this event schema:

```json
{
  "type": "object",
  "required": ["name"],
  "additionalProperties": {"type": "string"}
}
```

Using `schema_contract()` and `generate_python()` yields a Python event alias
equivalent to `dict[str, str]`. `TypeAdapter(models.EventsEvent).validate_python({})`
succeeds. The TypeScript result is a string-indexed map with no required `name`.

Expected behavior: `{"name":"ok"}` is valid; `{}` and `{"name":123}` are invalid.
The required key's value is governed by the additional-properties schema.

## Proposed implementation

Account for required keys outside `properties` when constructing the IR. For
supported object shapes, synthesize required fields with the applicable value
type while preserving additional-property handling.

Alternatively, reject unsupported shapes with an actionable `ContractError`.
Do not silently weaken them. Account for omitted/true `additionalProperties`,
typed additional properties, and the unsatisfiable case where a required
undeclared key is explicitly forbidden by `additionalProperties: false`.

## Acceptance criteria

- The reproduced contract either generates types that require `name` in both
  languages or is explicitly rejected during generation.
- If supported, Python validation and a TypeScript compile-time fixture reject
  `{}` and accept `{"name":"ok"}`; wrong value types are also rejected.
- Existing ordinary maps still accept `{}` when no key is required.
- Cover a mix of declared properties and required undeclared keys.
- Cover typed, unrestricted, omitted, and forbidden additional-property cases
  without losing the policy work from ticket 004.
- Validation/generation errors are actionable and occur before writing partial
  generated output.

## Validation

The shared object parser synthesizes required undeclared fields using the
additional-properties value schema, or JsonValue when unrestricted/omitted.
Existing ordinary map behavior and the explicit forbidden-extras policy remain
intact. Required undeclared keys forbidden by `additionalProperties: false`
raise an actionable `ContractError` before either CLI generator writes files.

Ten new regressions failed before implementation. Added typed/unrestricted/
omitted and mixed-property coverage, Python validation and strict consumer type
checks for both Python backends and TypeScript (including expected missing-key
and wrong-value errors). `uv run pytest -q --cov` passed **195 tests**, **90.20%**
coverage; `npm run test:coverage` passed **18 tests**. Pyright, TypeScript, Ruff,
Pylint, all pre-commit hooks and artifact drift checks passed. `uv build` and
`uv run python scripts/check_package.py` passed for core/HTTPX/HTTPX2 installs.
Compatibility runs passed **192 tests** each (3 snapshots deselected) on Python
3.12 with lowest dependencies (Pydantic 2.11.2), and Python 3.14 with latest
dependencies. No committed generated artifacts changed for this ticket.

Run schema-matrix and contract-boundary tests, strict type checks on the newly
generated Python and TypeScript packages, the complete Python suite, and artifact
drift checks.
