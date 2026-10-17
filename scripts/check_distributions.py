import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "fastapi-canon": ("fastapi-canon", "fastapi_canon"),
    "fastapi-streams": ("fastapi-streams", "fastapi_streams"),
    "fastapi-wsrpc": ("fastapi-wsrpc", "fastapi_wsrpc"),
}


def main() -> None:
    wheels = {}
    for name, (directory, module) in PACKAGES.items():
        output = ROOT / "dist" / name
        _run("uv", "build", "--package", name, "--out-dir", str(output))
        project = tomllib.loads(
            (ROOT / "packages" / directory / "pyproject.toml").read_text("utf-8")
        )["project"]
        (wheel,) = output.glob(f"{name.replace('-', '_')}-{project['version']}-*.whl")
        with zipfile.ZipFile(wheel) as artifact:
            assert f"{module}/py.typed" in artifact.namelist()
            assert not any(path.endswith("uv.lock") for path in artifact.namelist())
        (sdist,) = output.glob(f"{name.replace('-', '_')}-{project['version']}.tar.gz")
        _run(sys.executable, "-m", "twine", "check", "--strict", str(wheel), str(sdist))
        wheels[name] = str(wheel)

    combinations = (
        ("fastapi-canon",),
        ("fastapi-streams",),
        ("fastapi-wsrpc",),
        ("fastapi-canon[streams]", "fastapi-streams[codegen]"),
        ("fastapi-canon", "fastapi-wsrpc[codegen,dishka]"),
        (
            "fastapi-canon[streams]",
            "fastapi-streams[codegen]",
            "fastapi-wsrpc[codegen,dishka]",
        ),
    )
    for requirements in combinations:
        with tempfile.TemporaryDirectory(prefix="canon-artifacts-") as temporary:
            environment = Path(temporary) / "venv"
            _run("uv", "venv", "--python", sys.executable, str(environment))
            python = environment / (
                "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
            )
            artifacts = []
            for requirement in requirements:
                name, _, extras = requirement.partition("[")
                artifacts.append(wheels[name] + (f"[{extras}" if extras else ""))
            _run(
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                *artifacts,
                "httpx>=0.28",
            )
            _run("uv", "pip", "check", "--python", str(python))
            names = [requirement.split("[")[0] for requirement in requirements]
            _run(
                str(python),
                "-I",
                str(ROOT / "scripts/smoke_installed.py"),
                *names,
                cwd=Path(temporary),
            )
    _check_reference(wheels["fastapi-canon"])


def _check_reference(canon_wheel: str) -> None:
    reference = ROOT / "examples/reference-service"
    project = tomllib.loads((reference / "pyproject.toml").read_text("utf-8"))[
        "project"
    ]
    output = ROOT / "dist/reference-service"
    _run("uv", "build", "--package", project["name"], "--out-dir", str(output))
    (wheel,) = output.glob(f"fastapi_canon_reference-{project['version']}-*.whl")
    with tempfile.TemporaryDirectory(prefix="canon-reference-") as temporary:
        environment = Path(temporary) / "venv"
        _run("uv", "venv", "--python", sys.executable, str(environment))
        python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        _run(
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            canon_wheel,
            str(wheel),
            "httpx>=0.28",
            "pytest>=8.3",
            "pytest-asyncio>=1",
        )
        _run("uv", "pip", "check", "--python", str(python))
        _run(
            str(python),
            "-I",
            "-c",
            "import app, fastapi_canon, importlib.util, sys; from pathlib import Path; "
            "assert Path(app.__file__).resolve().is_relative_to(Path(sys.prefix)); "
            "assert Path(fastapi_canon.__file__).resolve()"
            ".is_relative_to(Path(sys.prefix)); "
            "assert importlib.util.find_spec('fastapi_streams') is None; "
            "assert importlib.util.find_spec('fastapi_wsrpc') is None",
            cwd=Path(temporary),
        )
        _run(
            str(python),
            "-I",
            "-m",
            "pytest",
            "-q",
            "-c",
            str(reference / "pyproject.toml"),
            str(reference / "tests"),
            cwd=Path(temporary),
        )


def _run(*command: str, cwd: Path = ROOT) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
