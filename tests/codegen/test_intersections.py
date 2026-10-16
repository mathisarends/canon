import pytest
from pydantic import TypeAdapter, ValidationError

from fastapi_streams.codegen.openapi import ContractError
from fastapi_streams.codegen.python import generate_python
from tests.codegen.helpers import load_models, schema_contract


@pytest.mark.parametrize("required_first", [False, True])
def test_allof_preserves_required_fields_in_either_order(tmp_path, required_first):
    optional = {"type": "object", "properties": {"x": {"type": "string"}}}
    required = {**optional, "required": ["x"]}
    members = [required, optional] if required_first else [optional, required]
    files = generate_python(schema_contract({"allOf": members}))
    with load_models(tmp_path, files) as models:
        adapter = TypeAdapter(models.EventsEvent)
        assert adapter.validate_python({"x": "ok"}).x == "ok"
        for invalid in ({}, {"x": None}):
            with pytest.raises(ValidationError):
                adapter.validate_python(invalid)


def test_conflicting_allof_fields_fail_generation():
    members = [
        {"type": "object", "properties": {"x": {"type": kind}}}
        for kind in ("string", "integer")
    ]
    with pytest.raises(ContractError, match="Conflicting allOf field: x"):
        generate_python(schema_contract({"allOf": members}))
