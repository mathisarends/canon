import sys
from pathlib import Path

from fastapi_streams.codegen.cli import main

ROOT = Path(__file__).resolve().parents[1]


def run() -> int:
    check = ["--check"] if "--check" in sys.argv else []
    applications = [
        ("examples.agent_runs:app", "schema/openapi.json", "examples/agent_runs"),
        (
            "tests.fixtures.models_app:app",
            "tests/fixtures/openapi.json",
            "tests/fixtures",
        ),
    ]
    result = 0
    for app, schema, output in applications:
        if not check:
            result |= main(["schema", "--app", app, "--output", str(ROOT / schema)])
        for language, directory in (
            ("typescript", "generated"),
            ("python", "generated_python"),
        ):
            result |= main(
                [
                    "check" if check else "generate",
                    "--schema",
                    str(ROOT / schema),
                    "--language",
                    language,
                    "--output",
                    str(ROOT / output / directory),
                    *(["--app", app] if check else []),
                ]
            )
    return result


if __name__ == "__main__":
    sys.exit(run())
