"""The core package must work even when the optional dependency is absent."""

import subprocess
import sys
import textwrap


def test_core_import_runtime_and_missing_extra_diagnostic() -> None:
    script = textwrap.dedent("""\
        import sys
        from importlib.abc import MetaPathFinder

        class NoStreams(MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "fastapi_streams" or fullname.startswith("fastapi_streams."):
                    raise ModuleNotFoundError("Streams deliberately unavailable", name=fullname)

        sys.meta_path.insert(0, NoStreams())
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from fastapi_canon import HTTPMethod, CanonRouter, Composition, Feature
        import fastapi_canon.integrations

        router = CanonRouter()
        @router.api_route("/health", methods=[HTTPMethod.GET])
        async def health() -> dict[str, str]:
            return {"status": "ok"}

        app = Composition(Feature(name="health", routers=[router])).apply(FastAPI())
        with TestClient(app) as client:
            assert client.get("/health").json() == {"status": "ok"}
        assert "/health" in app.openapi()["paths"]
        assert not any(name.startswith("fastapi_streams") for name in sys.modules)
        try:
            from fastapi_canon.integrations.streams import CanonStreamRouter
        except ModuleNotFoundError as exc:
            assert exc.name == "fastapi_streams"
            assert "fastapi-canon[streams]" in str(exc)
        else:
            raise AssertionError("The integration must require the optional dependency")
    """)
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
