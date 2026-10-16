"""Smoke-test the wheel for the current project version in isolated environments."""

import subprocess
import sys
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
    for core_only in (True, False):
        command = [
            "uv",
            "run",
            "--isolated",
            "--no-project",
            "--python",
            sys.executable,
        ]
        command += ["--with", str(wheels[0]) + ("" if core_only else "[codegen]")]
        if not core_only:
            command += ["--with", "httpx>=0.28"]
        command += [
            "python",
            "-I",
            str(ROOT / "scripts/smoke_package.py"),
            "--expected-version",
            version,
        ]
        if core_only:
            command.append("--core-only")
        subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
