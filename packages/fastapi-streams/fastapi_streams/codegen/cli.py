from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI

from fastapi_streams import __version__
from fastapi_streams.codegen.openapi import ContractError, Document, export_schema
from fastapi_streams.codegen.writer import write_files

if TYPE_CHECKING:
    from fastapi_streams.codegen.diagnostics import GenerationDiagnostic


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fastapi-streams")
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser("schema", help="Export and validate OpenAPI 3.2")
    schema.add_argument("--app", required=True)
    schema.add_argument("--output", required=True, type=Path)
    schema.add_argument("--check", action="store_true")
    for name in ("generate", "check"):
        command = commands.add_parser(
            name,
            help="Generate a client"
            if name == "generate"
            else "Check schema and generated-client drift",
        )
        command.add_argument("--schema", required=True, type=Path)
        command.add_argument(
            "--language", choices=["typescript", "python"], default="typescript"
        )
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--diagnostics", type=Path, help="Write JSON diagnostics")
        command.add_argument(
            "--strict", action="store_true", help="Fail on unaccepted diagnostics"
        )
        command.add_argument(
            "--allow-diagnostics",
            type=Path,
            help="JSON allowances with exact IDs and review reasons",
        )
        command.add_argument(
            "--python-http-client",
            choices=["httpx", "httpx2"],
            help="Python HTTP library (default: httpx; opt in with httpx2)",
        )
        if name == "generate":
            command.add_argument("--check", action="store_true")
        else:
            command.set_defaults(check=True)
            command.add_argument(
                "--app", help="Also compare the app's contract with --schema"
            )
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            content = (
                json.dumps(
                    export_schema(_load_app(args.app)),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
                + "\n"
            )
            output = cast(Path, args.output)
            if args.check:
                if not output.is_file() or output.read_bytes() != content.encode(
                    "utf-8"
                ):
                    print(f"Out of date: {output}", file=sys.stderr)
                    return 1
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(content, encoding="utf-8", newline="\n")
        else:
            if args.diagnostics:
                report = args.diagnostics.resolve()
                output = args.output.resolve()
                inputs = {args.schema.resolve()}
                if args.allow_diagnostics:
                    inputs.add(args.allow_diagnostics.resolve())
                if report in inputs or report == output or output in report.parents:
                    raise ContractError(
                        "--diagnostics must be outside the generated output "
                        "and input files"
                    )
            if args.language != "python" and args.python_http_client is not None:
                raise ContractError("--python-http-client requires --language python")
            from fastapi_streams.codegen.diagnostics import (
                accepted_diagnostics,
                emit_diagnostics,
            )
            from fastapi_streams.codegen.ir import build_ir
            from fastapi_streams.codegen.python import generate_python
            from fastapi_streams.codegen.typescript import generate_typescript

            document = json.loads(args.schema.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                raise ContractError("The OpenAPI document must be an object")
            document = cast(Document, document)
            generation = _generation_metadata(
                document, args.language, args.python_http_client or "httpx"
            )
            if args.command == "check" and args.app:
                expected = export_schema(_load_app(args.app))
                if expected != document:
                    print(
                        f"Out of date: {args.schema} (application contract changed)",
                        file=sys.stderr,
                    )
                    return 1
            diagnostics: list[GenerationDiagnostic] = []
            contract = build_ir(document, target=args.language, diagnostics=diagnostics)
            # Reports precede strict-policy failures, so CI can review new IDs.
            if args.diagnostics:
                _write_diagnostics(
                    args.diagnostics,
                    diagnostics,
                    set(),
                    generation,
                )
            accepted: set[str] = (
                accepted_diagnostics(
                    diagnostics, json.loads(args.allow_diagnostics.read_text("utf-8"))
                )
                if args.allow_diagnostics
                else set()
            )
            if args.diagnostics:
                _write_diagnostics(
                    args.diagnostics,
                    diagnostics,
                    accepted,
                    generation,
                )
            pending = [item for item in diagnostics if item.id not in accepted]
            emit_diagnostics(pending)
            if args.strict and pending:
                raise ContractError(
                    f"{len(pending)} unaccepted generation diagnostics; "
                    "review --diagnostics and provide explicit --allow-diagnostics"
                )
            generated = (
                generate_python(
                    contract, http_client=args.python_http_client or "httpx"
                )
                if args.language == "python"
                else generate_typescript(contract)
            )
            changed = write_files(
                args.output, generated, check=args.check, generation=generation
            )
            if args.check and changed:
                for path in changed:
                    print(f"Out of date: {path}", file=sys.stderr)
                return 1
    except (ContractError, OSError, ValueError, ImportError, AttributeError) as exc:
        message = str(exc)
        if isinstance(exc, ImportError) and exc.name in {"jinja2", "jsonschema"}:
            message = "Install fastapi-streams[codegen] to generate clients"
        print(f"fastapi-streams: {message}", file=sys.stderr)
        return 2
    return 0


def _load_app(value: str) -> FastAPI:
    module, separator, attribute = value.partition(":")
    if not separator or not module or not attribute:
        raise ContractError("--app must use module:attribute syntax")
    # Console scripts start with their installation directory on sys.path.
    sys.path.insert(0, str(Path.cwd()))
    app = getattr(importlib.import_module(module), attribute)
    if not isinstance(app, FastAPI):
        raise ContractError(f"{value} is not a FastAPI application")
    return app


def _generation_metadata(
    document: Document, target: str, http_client: str
) -> dict[str, str | None]:
    # Share canonical provenance between manifests and optional reports.
    encoded = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "generator": "fastapi-streams",
        "generator_version": __version__,
        "schema_sha256": hashlib.sha256(encoded).hexdigest(),
        "schema_hash_encoding": "canonical-json-v1",
        "target": target,
        "python_http_client": http_client if target == "python" else None,
    }


def _write_diagnostics(
    path: Path,
    diagnostics: list[GenerationDiagnostic],
    accepted: set[str],
    generation: dict[str, str | None],
) -> None:
    python = generation["target"] == "python"
    request_phase = "method_call" if python else "not_performed"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "generation": generation,
                "validation": {
                    "full_json_schema": False,
                    "runtime_scope": (
                        "generated_types_and_supported_constraints"
                        if python
                        else "json_decoding_only"
                    ),
                    "parameters": {
                        "phase": request_phase,
                        "schema_validation": python,
                    },
                    "request_body": {
                        "phase": request_phase,
                        "schema_validation": python,
                    },
                    "events": {
                        "phase": "iteration",
                        "schema_validation": python,
                        "json_decoding": True,
                    },
                    "http_error_bodies": {
                        "phase": "consumer_controlled",
                        "schema_validation": False,
                    },
                },
                "diagnostics": [
                    item.to_dict(accepted=item.id in accepted) for item in diagnostics
                ],
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    sys.exit(main())
