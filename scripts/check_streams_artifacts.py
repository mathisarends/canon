import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packages/fastapi-streams"


def main() -> None:
    version = tomllib.loads((PACKAGE / "pyproject.toml").read_text("utf-8"))["project"][
        "version"
    ]
    (wheel,) = (ROOT / "dist/fastapi-streams").glob(f"fastapi_streams-{version}-*.whl")
    for backend in (None, "httpx", "httpx2"):
        with tempfile.TemporaryDirectory(prefix="canon-streams-") as temporary:
            environment = Path(temporary) / "venv"
            _run("uv", "venv", "--python", sys.executable, str(environment))
            python = environment / (
                "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
            )
            requirements = [str(wheel)]
            flags = ["--core-only"]
            if backend:
                requirements = [str(wheel) + "[codegen]", backend]
                flags = ["--http-client", backend]
            _run("uv", "pip", "install", "--python", str(python), *requirements)
            _run(
                str(python),
                "-I",
                str(PACKAGE / "scripts/smoke_package.py"),
                "--expected-version",
                version,
                *flags,
            )


def _run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
