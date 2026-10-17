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
    "pyrpckit": ("websocket-rpc", "rpckit"),
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
        wheels[name] = str(wheel)

    combinations = (
        ("fastapi-canon",),
        ("fastapi-streams",),
        ("pyrpckit",),
        ("fastapi-canon[streams]", "fastapi-streams[codegen]"),
        ("fastapi-canon", "pyrpckit[codegen,dishka]"),
        (
            "fastapi-canon[streams]",
            "fastapi-streams[codegen]",
            "pyrpckit[codegen,dishka]",
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


def _run(*command: str, cwd: Path = ROOT) -> None:
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


if __name__ == "__main__":
    main()
