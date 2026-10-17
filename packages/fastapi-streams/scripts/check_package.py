"""Smoke-test the wheel for the current project version in isolated environments."""

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    name = project["name"].replace("-", "_")
    version = project["version"]
    wheels = list((ROOT / "dist").glob(f"{name}-{version}-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected one built wheel for {name} {version}; run uv build")
    for backend in (None, "httpx", "httpx2"):
        with tempfile.TemporaryDirectory(
            prefix="fastapi-streams-package-"
        ) as directory:
            environment = Path(directory) / "venv"
            subprocess.run(
                ["uv", "venv", "--python", sys.executable, str(environment)],
                cwd=ROOT,
                check=True,
            )
            python = environment / (
                "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
            )
            # Each build keeps the release version. Bypass cached local wheels so
            # smoke tests always install the artifact that was just built.
            install = [
                "uv",
                "pip",
                "install",
                "--python",
                str(python),
                "--no-cache",
                str(wheels[0]) + ("" if backend is None else "[codegen]"),
            ]
            if backend is not None:
                install.append(
                    "httpx2>=2.13.1,<3" if backend == "httpx2" else "httpx>=0.28"
                )
            subprocess.run(install, cwd=ROOT, check=True)
            command = [
                str(python),
                "-I",
                str(ROOT / "scripts/smoke_package.py"),
                "--expected-version",
                version,
            ]
            if backend is None:
                command.append("--core-only")
            else:
                command += ["--http-client", backend]
            subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
