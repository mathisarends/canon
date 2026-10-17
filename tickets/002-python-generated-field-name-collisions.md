# 002 — Avoid field-name collisions in generated Python models

Status: Complete
Priority: P2
Scope: Python naming, model generation, discriminator handling, typing tests
Integration: Complete before ticket 004, which also modifies model generation.

## Problem

Valid source models can produce a generated Python package that fails during
import. Field normalization protects Python keywords and `model_` names, but not
names used by generated type annotations or helper decorators.

Confirmed optional field names include `int`, `str`, `list`, and
`field_validator`. A source model created with resolved runtime annotations is
valid, but the generated module uses postponed annotations and `None` defaults.
Those defaults shadow annotation names during Pydantic's annotation resolution.

## Relevant code

- `fastapi_streams/codegen/names.py`: `python_identifier()`.
- `fastapi_streams/codegen/python.py`: `_Models.render()`, field naming and
  assignment generation (review baseline: lines 294–343), and generated
  `@field_validator` use.
- `_Models.render_type()`: discriminator property-name conversion must stay
  consistent if field names are escaped.
- `tests/codegen/helpers.py`: `event_contract()`, `load_models()`, `load_package()`.

## Reproduction

```python
source = create_model("Event", list=(list[str], []))
files = generate_python(event_contract(source))
with load_models(tmp_path, files):
    pass
```

The generated model contains:

```python
class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    list: list[str] | None = None
```

Import raises `TypeError: 'NoneType' object is not subscriptable`.

Additional independently reproduced cases:

| Source definition passed to `create_model` | Generated import failure |
| --- | --- |
| `int=(int, 1)` | `TypeError` resolving `int | None` |
| `str=(str, "x")` | `TypeError` resolving `str | None` |
| `field_validator=(str, "x")` | `TypeError: 'NoneType' object is not callable` at the generated decorator |

## Proposed implementation

Reserve or qualify symbols used by generated model annotations and helpers.
If a field is renamed, preserve its original JSON property name with `Field`
aliases. Use a consistent mapping for definitions, validators, and union
discriminators. Avoid changing unrelated operation parameter names as an
accidental consequence of changing a shared naming utility.

Re-check collisions after escaping: a protected field and an existing suffixed
field must not silently overwrite one another. Do not rely on a finite list of
the four reproduced names if other generated imports have the same problem.

## Acceptance criteria

- All four source models above generate importable Python packages.
- Generated models accept and serialize the original wire names without data
  loss, including explicit values and omitted optional fields.
- Explicit null remains rejected for fields that are optional but non-nullable.
- The naming strategy also works for nested objects and discriminators that use
  an escaped property name.
- Post-normalization collisions fail with an actionable `ContractError` or are
  resolved deterministically without changing wire keys.
- Generated packages and valid consumer calls pass strict Pyright checks.
- Add regression tests that import and use generated models, not only snapshots.

## Validation

Implemented model-only symbol escaping with wire aliases and the same mapping
for fields, validators and discriminators. All symbols used by generated model
annotations/decorators are protected; operation parameter names are unchanged.
Post-escape collisions raise `ContractError`.

The four import reproductions failed before the fix. Added package import,
omission/null, round-trip, nested model and escaped-discriminator regressions,
plus a strict Pyright consumer fixture. `uv run pytest -q` passed **142 tests**;
the schema matrix checks both generated Python backends and TypeScript.
`uv run pyright`, Ruff lint/format and `uv run python scripts/codegen.py --check`
passed; committed generated artifacts are unchanged.

Run focused model, discriminator, and Python typing tests, then the Python suite
and `uv run pyright`. Regenerate committed artifacts if the naming strategy
changes existing output, and run the drift check.
