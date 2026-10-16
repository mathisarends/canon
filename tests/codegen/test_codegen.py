import json
from pathlib import Path

import pytest

from examples.agent_runs import app
from fastapi_streams.codegen.cli import main
from fastapi_streams.codegen.ir import Reference, Union, build_ir
from fastapi_streams.codegen.openapi import ContractError, export_schema
from fastapi_streams.codegen.typescript import generate_typescript
from fastapi_streams.codegen.writer import MANIFEST, write_files


def test_ir_and_types_are_typed_and_streams_only():
    contract = build_ir(export_schema(app))
    assert {op.operation_id for op in contract.operations} == {
        "stream_run_events",
        "stream_prompt",
    }
    assert all(op.group == "agentRuns" for op in contract.operations)
    event = next(
        declaration
        for declaration in contract.declarations
        if declaration.name == "RunEvent"
    )
    assert isinstance(event.type, Union)
    assert event.type.discriminator == "type"
    assert all(isinstance(member, Reference) for member in event.type.members)
    files = generate_typescript(contract)
    assert files == generate_typescript(build_ir(export_schema(app)))
    assert '"token.delta"' in files["types.ts"]
    assert "AsyncIterable<Types.RunEvent>" in files["agent-runs/api.ts"]
    assert "health" not in files["client.ts"]
    assert "any" not in files["types.ts"]
    assert "unknown" not in files["types.ts"]
    assert contract.security_schemes[0].kind == "http"


def test_cli_export_generate_and_check(tmp_path):
    schema = tmp_path / "schema.json"
    output = tmp_path / "sdk"
    args = ["schema", "--app", "examples.agent_runs:app", "--output", str(schema)]
    assert main(args + ["--check"]) == 1
    assert not schema.exists()
    assert main(args) == 0
    assert main(args + ["--check"]) == 0
    args = ["generate", "--schema", str(schema), "--output", str(output)]
    assert main(args + ["--check"]) == 1
    assert not output.exists()
    assert main(args) == 0
    assert main(args + ["--check"]) == 0
    (output / "types.ts").write_text("stale")
    assert main(args + ["--check"]) == 1
    assert main(args) == 0
    assert main(args + ["--check"]) == 0


def test_writer_removes_only_owned_files_and_checks_stale(tmp_path):
    write_files(tmp_path, {"old/api.ts": "old"})
    (tmp_path / "handwritten.ts").write_text("keep")
    assert tmp_path / "old/api.ts" in write_files(
        tmp_path, {"new.ts": "new"}, check=True
    )
    assert (tmp_path / "old/api.ts").exists()
    write_files(tmp_path, {"new.ts": "new"})
    assert not (tmp_path / "old/api.ts").exists()
    assert (tmp_path / "handwritten.ts").read_text() == "keep"
    assert not write_files(tmp_path, {"new.ts": "new"}, check=True)


def test_writer_preflights_unsafe_manifest_before_any_write(tmp_path):
    (tmp_path / MANIFEST).write_text(json.dumps({"files": ["../outside.ts"]}))
    with pytest.raises(ValueError, match="Unsafe"):
        write_files(tmp_path, {"safe.ts": "new"})
    assert not (tmp_path / "safe.ts").exists()


def test_generator_rejects_untyped_streams_and_name_collisions():
    document = export_schema(app)
    operation = document["paths"]["/v1/runs/{run_id}/events"]["get"]
    operation["responses"]["200"]["content"]["text/event-stream"]["itemSchema"] = {}
    with pytest.raises(ContractError, match="contentSchema"):
        build_ir(document)
    document = export_schema(app)
    document["paths"]["/v1/runs/{run_id}/events"]["post"]["operationId"] = (
        "stream_run_events"
    )
    with pytest.raises(ContractError, match="duplicate"):
        build_ir(document)


def test_example_contract_snapshot():
    snapshot = Path(__file__).parents[2] / "schema/openapi.json"
    assert json.loads(snapshot.read_text(encoding="utf-8")) == export_schema(app)


@pytest.mark.parametrize("language", ["typescript", "python"])
def test_check_command_detects_both_contract_and_client_drift(tmp_path, language):
    schema = tmp_path / "openapi.json"
    output = tmp_path / "sdk"
    assert (
        main(["schema", "--app", "examples.agent_runs:app", "--output", str(schema)])
        == 0
    )
    flags = ["--schema", str(schema), "--language", language, "--output", str(output)]
    assert main(["generate", *flags]) == 0
    check = ["check", "--app", "examples.agent_runs:app", *flags]
    assert main(check) == 0
    model = output / ("types.ts" if language == "typescript" else "models.py")
    model.write_text("stale")
    assert main(check) == 1
    assert model.read_text() == "stale"
    assert main(["generate", *flags]) == 0
    document = json.loads(schema.read_text())
    document["info"]["title"] = "old title"
    schema.write_text(json.dumps(document))
    before = schema.read_bytes()
    assert main(check) == 1
    assert schema.read_bytes() == before
