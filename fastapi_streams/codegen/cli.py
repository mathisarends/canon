import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import cast

from fastapi import FastAPI

from fastapi_streams.codegen.openapi import ContractError, Document, export_schema
from fastapi_streams.codegen.writer import write_files


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fastapi-streams")
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser("schema", help="Export and validate OpenAPI 3.2")
    schema.add_argument("--app", required=True)
    schema.add_argument("--output", required=True, type=Path)
    schema.add_argument("--check", action="store_true")
    generate = commands.add_parser("generate", help="Generate a typed streaming SDK")
    generate.add_argument("--schema", required=True, type=Path)
    generate.add_argument(
        "--language", choices=["typescript", "python"], default="typescript"
    )
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--check", action="store_true")
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
            from fastapi_streams.codegen.ir import build_ir
            from fastapi_streams.codegen.python import generate_python
            from fastapi_streams.codegen.typescript import generate_typescript

            document = json.loads(args.schema.read_text(encoding="utf-8"))
            if not isinstance(document, dict):
                raise ContractError("The OpenAPI document must be an object")
            contract = build_ir(cast(Document, document))
            render = (
                generate_python if args.language == "python" else generate_typescript
            )
            changed = write_files(args.output, render(contract), check=args.check)
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


if __name__ == "__main__":
    sys.exit(main())
