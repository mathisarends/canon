import json
from pathlib import Path

import httpx
import pytest
from pydantic import TypeAdapter, ValidationError

from fastapi_streams.codegen.ir import build_ir
from fastapi_streams.codegen.openapi import (
    ContractError,
    export_schema,
    validate_contract,
)
from fastapi_streams.codegen.python import generate_python
from fastapi_streams.codegen.typescript import generate_typescript
from fastapi_streams.codegen.writer import write_files
from tests.fixtures.generated_python import Client
from tests.fixtures.generated_python.models import (
    FixtureEvent,
    Metadata,
    MetadataMode,
    NestedEvent,
)
from tests.fixtures.models_app import app


async def test_nested_python_models_and_parameters():
    payload = {
        "type": "nested",
        "external-id": "1",
        "metadata": {
            "labels": ["typed"],
            "limits": {"max": 3},
            "note": None,
            "mode": "fast",
        },
        "children": [],
    }

    async def handler(request):
        assert request.url.params.get_list("labels") == ["a", "b"]
        assert request.headers["x-trace"] == "trace"
        return httpx.Response(
            200,
            content="data: " + json.dumps(payload) + "\n\n",
            headers={"Content-Type": "text/event-stream"},
        )

    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http,
        Client("http://example.test", http_client=http) as client,
    ):
        events = [
            event
            async for event in client.fixtures.nested_events(
                item_id=1, labels=["a", "b"], x_trace="trace"
            )
        ]
    assert isinstance(events[0], NestedEvent)
    assert events[0].external_id == "1"
    assert isinstance(events[0].metadata, Metadata)
    assert events[0].metadata.limits == {"max": 3}
    assert events[0].metadata.mode is MetadataMode.FAST
    assert events[0].children == []
    assert TypeAdapter(FixtureEvent).validate_python(payload).type == "nested"
    with pytest.raises(ValidationError):
        TypeAdapter(FixtureEvent).validate_python({**payload, "children": None})
    with pytest.raises(ValidationError):
        TypeAdapter(FixtureEvent).validate_python(
            {**payload, "metadata": {**payload["metadata"], "limits": {"max": "bad"}}}
        )


def test_fixture_generation_is_current():
    document = export_schema(app)
    assert json.loads(Path("tests/fixtures/openapi.json").read_text()) == document
    contract = build_ir(document)
    assert not write_files(
        Path("tests/fixtures/generated"), generate_typescript(contract), check=True
    )
    assert not write_files(
        Path("tests/fixtures/generated_python"), generate_python(contract), check=True
    )


def test_refs_in_properties_named_like_schema_annotations_are_checked():
    document = export_schema(app)
    document["components"]["schemas"]["Bad"] = {
        "type": "object",
        "properties": {"default": {"$ref": "#/missing"}},
    }
    with pytest.raises(ContractError, match="Unresolved"):
        validate_contract(document)
    document["components"]["schemas"]["Bad"] = {"default": {"$ref": "example-data"}}
    validate_contract(document)


def test_array_path_parameters_fail_before_rendering():
    document = export_schema(app)
    operation = document["paths"]["/nested/{item_id}"]["get"]
    path = next(param for param in operation["parameters"] if param["in"] == "path")
    path["schema"] = {"type": "array", "items": {"type": "string"}}
    with pytest.raises(ContractError, match="parameters"):
        build_ir(document)
