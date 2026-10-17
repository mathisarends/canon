import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from fastapi_streams.codegen.ir import Reference
from fastapi_streams.codegen.python import generate_python
from fastapi_streams.codegen.typescript import generate_typescript
from fastapi_streams.codegen.writer import write_files
from tests.codegen.helpers import load_models, schema_contract

ROOT = Path(__file__).parents[2]
CASES = [
    ("string", {"type": "string"}, {}, "hello", []),
    ("number", {"type": "number"}, {}, 1.5, {}),
    ("boolean", {"type": "boolean"}, {}, True, "invalid"),
    ("null", {"type": "null"}, {}, None, 1),
    ("array", {"type": "array", "items": {"type": "integer"}}, {}, [1, 2], ["bad"]),
    ("union", {"anyOf": [{"type": "string"}, {"type": "integer"}]}, {}, "ok", []),
    (
        "map",
        {"type": "object", "additionalProperties": {"type": "integer"}},
        {},
        {"x": 1},
        {"x": "bad"},
    ),
    (
        "enum",
        {"$ref": "#/components/schemas/Mode"},
        {"Mode": {"type": "string", "enum": ["fast", "full"]}},
        "fast",
        "bad",
    ),
    (
        "object",
        {
            "type": "object",
            "properties": {
                "external-id": {"type": "string"},
                "note": {"type": ["string", "null"]},
                "count": {"type": "integer"},
            },
            "required": ["external-id"],
        },
        {},
        {"external-id": "x", "note": None},
        {"external-id": "x", "count": None},
    ),
    (
        "typed_extras",
        {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": {"type": "integer"},
        },
        {},
        {"name": "x", "extra": 1},
        {"name": "x", "extra": "bad"},
    ),
    (
        "recursive",
        {"$ref": "#/components/schemas/Node"},
        {
            "Node": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "children": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Node"},
                    },
                },
                "required": ["name", "children"],
            }
        },
        {
            "name": "root",
            "children": [
                {"name": "child", "children": [{"name": "leaf", "children": []}]}
            ],
        },
        {"name": "root", "children": [{"name": None, "children": []}]},
    ),
    (
        "intersection",
        {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"x": {"type": "string"}},
                    "required": ["x"],
                },
                {
                    "type": "object",
                    "properties": {"y": {"type": "integer"}},
                    "required": ["y"],
                },
            ]
        },
        {},
        {"x": "ok", "y": 1},
        {"x": "ok"},
    ),
]

for discriminator, values in [("event-type", ["a"]), ("type", ["a1", "a2"])]:
    CASES.append(
        (
            "discriminator_" + discriminator,
            {
                "oneOf": [
                    {"$ref": "#/components/schemas/A"},
                    {"$ref": "#/components/schemas/B"},
                ],
                "discriminator": {"propertyName": discriminator},
            },
            {
                "A": {
                    "type": "object",
                    "properties": {discriminator: {"type": "string", "enum": values}},
                    "required": [discriminator],
                },
                "B": {
                    "type": "object",
                    "properties": {discriminator: {"type": "string", "const": "b"}},
                    "required": [discriminator],
                },
            },
            {discriminator: values[-1]},
            {discriminator: "unknown"},
        )
    )


@pytest.fixture(scope="module")
def generated_matrix(tmp_path_factory):
    root = tmp_path_factory.mktemp("schema_matrix")
    generated = {}
    for name, schema, components, valid, invalid in CASES:
        contract = schema_contract(schema, components)
        python = generate_python(contract)
        write_files(root / name / "python", python)
        write_files(
            root / name / "python_httpx2",
            generate_python(contract, http_client="httpx2"),
        )
        write_files(root / name / "typescript", generate_typescript(contract))
        event = contract.operations[0].event
        event_name = event.name if isinstance(event, Reference) else "EventsEvent"
        generated[name] = (root / name / "python", python, event_name, valid, invalid)
    return root, generated


@pytest.mark.parametrize("name", [case[0] for case in CASES])
def test_generated_python_validates_supported_schema_matrix(generated_matrix, name):
    _, generated = generated_matrix
    path, files, event_name, valid, invalid = generated[name]
    with load_models(path, files) as models:
        adapter = TypeAdapter(getattr(models, event_name))
        parsed = adapter.validate_python(valid)
        assert (
            json.loads(adapter.dump_json(parsed, by_alias=True, exclude_unset=True))
            == valid
        )
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid)


def test_every_generated_package_passes_strict_typechecking(generated_matrix):
    root, _ = generated_matrix
    node = shutil.which("node")
    compiler = ROOT / "node_modules/typescript/bin/tsc"
    assert node and compiler.is_file(), (
        "Run npm ci before the generator acceptance tests"
    )
    config = root / "tsconfig.json"
    config.write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "strict": True,
                    "exactOptionalPropertyTypes": True,
                    "target": "ES2022",
                    "module": "ESNext",
                    "moduleResolution": "Bundler",
                    "noEmit": True,
                    "skipLibCheck": True,
                },
                "include": ["**/typescript/**/*.ts"],
            }
        )
    )
    result = subprocess.run(
        [node, str(compiler), "-p", str(config)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    pyright_config = root / "pyrightconfig.json"
    pyright_config.write_text(
        json.dumps(
            {
                "include": ["**/python", "**/python_httpx2"],
                "typeCheckingMode": "strict",
                "pythonVersion": "3.12",
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--project",
            str(pyright_config),
            "--pythonpath",
            sys.executable,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
