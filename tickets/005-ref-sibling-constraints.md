# 005 — Preserve or explicitly reject constraints alongside schema references

Status: Open
Priority: P2
Scope: Shared schema-to-IR parsing, both generators, contract boundary tests
Integration: After 004; before 006 because both modify object/reference parsing.

## Problem

When a Schema Object contains `$ref`, `_Types.parse()` only considers a small
set of sibling keywords before returning `Reference(name)`. In particular,
`enum` and `const` restrictions alongside a reference are silently discarded.

The contract is accepted, but both generated SDKs describe a broader set of
values. Python runtime validation also accepts values the source schema rejects.
This is a semantic restriction that the generators otherwise support, not just
an unexpressed numeric refinement in TypeScript.

## Relevant code

- `fastapi_streams/codegen/ir.py`: `_Types.parse()` `$ref` branch, especially
  the sibling-keyword check (review baseline: lines 366–372).
- `fastapi_streams/codegen/openapi.py`: reference resolution must retain its
  cycle and local-reference validation behavior.
- `tests/codegen/test_contract_boundaries.py`, `test_schema_matrix.py`, and
  `test_intersections.py`.

## Reproduction

```python
contract = schema_contract(
    {"$ref": "#/components/schemas/Name", "enum": ["allowed"]},
    {"Name": {"type": "string"}},
)
files = generate_python(contract)
```

The operation's generated event type is `Name = str`. Loading the model and
running `TypeAdapter(models.Name).validate_python("forbidden")` succeeds.
The TypeScript event type is likewise the unrestricted referenced string type.
The sibling enum has vanished from the IR.

## Proposed implementation

Interpret applicable sibling constraints conjunctively with the referenced
schema. Where the IR/generator cannot represent the combination, raise a
specific `ContractError` rather than silently accepting a weakened contract.

Audit other semantic siblings, including `required` and `additionalProperties`,
without attempting to implement every JSON Schema keyword in this ticket.
Metadata-only siblings such as `description` should continue working.
Do not reject ordinary annotated references just because they have metadata.

## Acceptance criteria

- `$ref` plus `enum` and `$ref` plus `const` either preserve their restrictions
  through both generators or fail explicitly before writing a client.
- If supported, Python rejects `"forbidden"` and TypeScript rejects the same
  value in a compile-time consumer fixture for the reproduced case.
- Include accepted-value coverage as well as rejected-value coverage.
- Test semantic siblings on object references; unsupported combinations must
  not silently broaden the accepted schema.
- Metadata-only siblings and recursive local references still work.
- Existing reference-cycle, unresolved-reference, and collision checks remain
  intact. CLI failures use the existing invalid-input error path.

## Validation

Run contract-boundary, schema-matrix, and intersection tests; type-check any
newly generated packages in both languages; run the complete Python suite and
artifact drift checks.
