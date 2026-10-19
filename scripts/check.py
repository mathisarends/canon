import argparse
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = (
    ROOT / "packages/fastapi-canon",
    ROOT / "packages/fastapi-streams",
    ROOT / "packages/fastapi-rpckit",
    ROOT / "examples/reference-service",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Canon workspace quality gates")
    parser.add_argument("gate", choices=("all", "lint", "types", "test", "clients"))
    args = parser.parse_args()
    gates = ("lint", "types", "test", "clients") if args.gate == "all" else (args.gate,)
    for gate in gates:
        if gate == "lint":
            _run(ROOT, "scripts/check_documentation.py")
            for root in (ROOT, *MEMBERS):
                targets = (
                    ("scripts", "tests", "examples/stack_service.py")
                    if root == ROOT
                    else (".",)
                )
                _run(root, "-m", "ruff", "check", *targets)
                _run(root, "-m", "ruff", "format", "--check", *targets)
        elif gate == "types":
            _run(MEMBERS[0], "-m", "mypy")
            _run(MEMBERS[1], "-m", "pyright", "--pythonpath", sys.executable)
            _run(MEMBERS[1], "-m", "pylint", "fastapi_streams")
            # Verify the installed public package; editable path discovery differs
            # between Pyright and Python, especially in a Windows workspace.
            _run(
                ROOT,
                "uv",
                "build",
                "--package",
                "fastapi-rpckit",
                "--out-dir",
                str(ROOT / "dist/fastapi-rpckit"),
                python=False,
            )
            metadata = tomllib.loads((MEMBERS[2] / "pyproject.toml").read_text("utf-8"))
            version = metadata["project"]["version"]
            (wheel,) = (ROOT / "dist/fastapi-rpckit").glob(
                f"fastapi_rpckit-{version}-*.whl"
            )
            _run(
                MEMBERS[2],
                "uv",
                "run",
                "--isolated",
                "--no-project",
                "--no-cache",
                "--python",
                sys.executable,
                "--with",
                str(wheel) + "[codegen,dishka,otel]",
                "--with",
                "pyright==1.1.414",
                "python",
                "scripts/verify_types.py",
                python=False,
            )
            _run(MEMBERS[3], "-m", "mypy", "src", "tests")
        elif gate == "test":
            for root in (*MEMBERS, ROOT):
                _run(root, "-m", "pytest", "-q")
        elif gate == "clients":
            for config in (
                "examples/generated_clients/rpcgen.toml",
                "examples/socket_protocol/rpcgen.toml",
            ):
                _run(
                    MEMBERS[2],
                    "-m",
                    "fastapi_rpckit.codegen.cli",
                    "generate",
                    "--config",
                    config,
                    "--check",
                )
            _run(MEMBERS[1], "scripts/codegen.py", "--check")
            npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
            if npm is None:
                raise SystemExit("npm is required for TypeScript client checks")
            for task in ("typecheck", "test:coverage"):
                _run(MEMBERS[1], npm, "run", task, python=False)


def _run(root: Path, *arguments: str, python: bool = True) -> None:
    command = [sys.executable, *arguments] if python else list(arguments)
    print(f"[{root.relative_to(ROOT) or '.'}] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=root, check=True)


if __name__ == "__main__":
    main()
