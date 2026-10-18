import argparse
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_documentation(root: Path = ROOT) -> list[str]:
    """Check active installation examples, leaving historical records intact."""
    errors: list[str] = []
    canon = tomllib.loads(
        (root / "packages/fastapi-canon/pyproject.toml").read_text("utf-8")
    )
    (pin,) = canon["project"]["optional-dependencies"]["streams"]
    expected = pin.split("==")[1]
    for name in (
        "packages/fastapi-canon/docs/streams.md",
        "packages/fastapi-canon/examples/streams/README.md",
    ):
        text = (root / name).read_text("utf-8")
        for version in re.findall(r"fastapi-streams(?:\[codegen\])?==([\w.]+)", text):
            if version != expected:
                errors.append(f"{name}: Streams {version} does not match {expected}")
    readme = (root / "packages/fastapi-streams/README.md").read_text("utf-8")
    if "git+https://github.com/mathisarends/fastapi-streams" in readme:
        errors.append("Streams quickstart must install the PyPI distribution")
    rpc = root / "packages/fastapi-rpckit"
    for folder in ("docs", "examples"):
        for path in (rpc / folder).rglob("*.md"):
            if "from fastapi_rpckit.integrations.fastapi import" in path.read_text(
                "utf-8"
            ):
                errors.append(
                    f"{path.relative_to(root)}: use package-root FastAPI imports"
                )
    source = (rpc / "fastapi_rpckit/integrations/dishka.py").read_text("utf-8")
    if "'fastapi'" in source or "[fastapi]" in source:
        errors.append("Dishka diagnostic must not suggest the removed fastapi extra")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    failures = check_documentation(parser.parse_args().root)
    for failure in failures:
        print(failure)
    raise SystemExit(bool(failures))
