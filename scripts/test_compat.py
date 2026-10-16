"""Run the dependency compatibility suite without changing uv.lock or .venv."""

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", choices=["3.12", "3.13", "3.14"], required=True)
    parser.add_argument("--dependencies", choices=["lowest", "latest"], required=True)
    args = parser.parse_args()
    label = f"{args.python}-{args.dependencies}"
    environment = ROOT / ".pytest_cache" / "compat-env" / label
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    def run(*command):
        subprocess.run(command, cwd=ROOT, check=True)

    run("uv", "venv", "--python", args.python, "--allow-existing", str(environment))
    run(
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        "--upgrade",
        "--resolution",
        "lowest-direct" if args.dependencies == "lowest" else "highest",
        "--only-binary",
        ":all:",
        "-r",
        "pyproject.toml",
        "--extra",
        "codegen",
    )
    # Keep test tooling current; only the published runtime/codegen bounds vary.
    run("uv", "pip", "install", "--python", str(python), "--group", "test")
    run("uv", "pip", "install", "--python", str(python), "--no-deps", "--editable", ".")
    run("uv", "pip", "check", "--python", str(python))
    report = ROOT / ".pytest_cache" / f"dependencies-{label}.txt"
    with report.open("w", encoding="utf-8") as output:
        subprocess.run(
            ["uv", "pip", "freeze", "--python", str(python)], check=True, stdout=output
        )
    print(report.read_text(), flush=True)
    run(
        str(python),
        "-m",
        "pytest",
        "-q",
        "-m",
        "not snapshot",
        "--basetemp",
        str(ROOT / ".pytest_cache" / f"tests-{label}"),
        "--junitxml",
        str(ROOT / ".pytest_cache" / f"results-{label}.xml"),
    )


if __name__ == "__main__":
    main()
