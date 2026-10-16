import importlib.util
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

import fastapi_streams
from fastapi_streams import StreamRouter


class Event(BaseModel):
    type: Literal["event"] = "event"
    text: str


def main() -> None:
    assert "site-packages" in str(Path(fastapi_streams.__file__).resolve())
    router = StreamRouter()

    @router.stream("/events", operation_id="events")
    async def events() -> AsyncIterator[Event]:
        yield Event(text="packaged")

    app = FastAPI()
    app.include_router(router)
    assert "/events" in app.openapi()["paths"]
    if "--core-only" in sys.argv:
        assert importlib.util.find_spec("jinja2") is None
        assert importlib.util.find_spec("jsonschema") is None
        from fastapi_streams.codegen.cli import main as cli

        assert callable(cli)
        print("Installed core imports without codegen dependencies")
        return

    from fastapi_streams.codegen.ir import build_ir
    from fastapi_streams.codegen.openapi import export_schema
    from fastapi_streams.codegen.python import generate_python
    from fastapi_streams.codegen.typescript import generate_typescript

    contract = build_ir(export_schema(app))
    assert "client.ts" in generate_typescript(contract)
    generated = generate_python(contract)
    assert "class EventType(StrEnum)" in generated["models.py"]
    assert "TypeAdapter" in generated["runtime.py"]
    print("Installed codegen loads its schemas and both client templates")


if __name__ == "__main__":
    main()
