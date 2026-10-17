"""Validate a release tag without importing or executing the package."""

import argparse
import ast
import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMBER = r"(?:0|[1-9][0-9]*)"
RELEASE_TAG = re.compile(rf"v{NUMBER}\.{NUMBER}\.{NUMBER}(?:(?:a|b|rc){NUMBER})?")


def check_release(tag: str, root: Path = ROOT) -> str:
    """Return the version if the tag, source versions and main ancestry agree."""
    if RELEASE_TAG.fullmatch(tag) is None:
        raise ValueError("Use vX.Y.Z or a prerelease such as vX.Y.Zrc1")
    version = tag[1:]
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    if project["version"] != version:
        raise ValueError("Tag does not match pyproject.toml project.version")

    module = ast.parse(
        (root / "fastapi_streams/__init__.py").read_text(encoding="utf-8")
    )
    versions = [
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
    ]
    if versions != [version]:
        raise ValueError("Tag does not match fastapi_streams.__version__")

    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    locked = [p["version"] for p in lock["package"] if p["name"] == project["name"]]
    if locked != [version]:
        raise ValueError("Tag does not match uv.lock; run uv lock after version bumps")

    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "refs/remotes/origin/main"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("Release commit must be on origin/main; fetch main first")
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Release tag, e.g. v0.0.1 or v0.1.0rc1")
    args = parser.parse_args()
    try:
        version = check_release(args.tag)
    except ValueError as error:
        parser.exit(1, f"Release validation failed: {error}\n")
    print(f"version={version}")
    print(f"prerelease={str(any(c.isalpha() for c in version)).lower()}")


if __name__ == "__main__":
    main()
