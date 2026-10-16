from copy import deepcopy

import pytest

from fastapi_streams.codegen.ir import build_ir
from fastapi_streams.codegen.openapi import ContractError
from fastapi_streams.codegen.python import generate_python
from fastapi_streams.codegen.typescript import generate_typescript
from tests.codegen.helpers import event_document, schema_contract


@pytest.mark.parametrize(
    ("schema", "components", "message"),
    [
        ({"$ref": "https://example.test/schema.json"}, {}, "Only local"),
        ({"$ref": "#/components/schemas/Missing"}, {}, "Unresolved reference"),
        (
            {"$ref": "#/components/schemas/A"},
            {
                "A": {"$ref": "#/components/schemas/B"},
                "B": {"$ref": "#/components/schemas/A"},
            },
            "Cyclic reference",
        ),
        ({"type": "array", "prefixItems": [{"type": "integer"}]}, {}, "Tuple schemas"),
        ({"const": {"x": 1}}, {}, "Object and array"),
        (
            {"$ref": "#/components/schemas/Event"},
            {
                "Event": {
                    "type": "object",
                    "properties": {"kind": {"enum": ["a-b", "a_b"]}},
                }
            },
            "Enum member names collide",
        ),
    ],
)
def test_unsupported_schema_contracts_fail_explicitly(schema, components, message):
    with pytest.raises(ContractError, match=message):
        schema_contract(schema, components)


@pytest.mark.parametrize(
    "case",
    [
        "cookie",
        "deep_object",
        "reserved_query",
        "multipart",
        "put",
        "multiple_success",
        "missing_id",
        "duplicate_name",
        "reserved_tag",
    ],
)
def test_unsupported_http_contracts_fail_explicitly(case):
    document = event_document(str)
    operation = document["paths"]["/events"]["get"]
    if case in {"cookie", "deep_object", "reserved_query"}:
        parameter = {"name": "value", "in": "query", "schema": {"type": "string"}}
        if case == "cookie":
            parameter["in"] = "cookie"
        elif case == "deep_object":
            parameter["style"] = "deepObject"
        else:
            parameter["allowReserved"] = True
        operation["parameters"] = [parameter]
    elif case == "multipart":
        document["paths"]["/events"] = {"post": operation}
        operation["requestBody"] = {
            "content": {"multipart/form-data": {"schema": {"type": "object"}}}
        }
    elif case == "put":
        document["paths"]["/events"] = {"put": operation}
    elif case == "multiple_success":
        operation["responses"]["201"] = deepcopy(operation["responses"]["200"])
    elif case == "missing_id":
        del operation["operationId"]
    elif case == "duplicate_name":
        other = deepcopy(operation)
        operation["operationId"], other["operationId"] = "a-b", "a_b"
        document["paths"]["/other"] = {"get": other}
    else:
        operation["tags"] = ["transport"]
    with pytest.raises(ContractError):
        build_ir(document)


@pytest.mark.parametrize(
    ("name", "render"),
    [("Client", generate_typescript), ("BaseModel", generate_python)],
)
def test_reserved_public_model_names_fail_generation(name, render):
    contract = schema_contract(
        {"$ref": f"#/components/schemas/{name}"},
        {name: {"type": "object", "properties": {"x": {"type": "string"}}}},
    )
    with pytest.raises(ContractError, match="Reserved"):
        render(contract)
