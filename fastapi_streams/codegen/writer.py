import json
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any, cast

MANIFEST = ".fastapi-streams.json"


def _owned_path(root: Path, relative: str) -> Path:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe generated path: {relative!r}")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()) or resolved == root.resolve():
        raise ValueError(f"Generated path escapes output directory: {relative!r}")
    return resolved


def write_files(
    output: Path, files: Mapping[str, str], *, check: bool = False
) -> tuple[Path, ...]:
    """Write deterministic output; only remove stale files owned by the manifest.

    Check mode is read-only, including when output does not yet exist.
    """
    expected = dict(files)
    if MANIFEST in expected:
        raise ValueError(f"{MANIFEST} is reserved")
    expected[MANIFEST] = json.dumps({"files": sorted(files)}, indent=2) + "\n"
    manifest = _owned_path(output, MANIFEST)
    previous: set[str] = set()
    if manifest.exists():
        value = json.loads(manifest.read_text(encoding="utf-8"))
        names = value.get("files")
        if not isinstance(names, list) or not all(
            isinstance(name, str) for name in cast(list[Any], names)
        ):
            raise ValueError(f"Invalid generated manifest: {manifest}")
        previous = set(cast(list[str], names))
    # Preflight every target, including stale paths, before modifying anything.
    paths = {name: _owned_path(output, name) for name in set(expected) | previous}
    changed: list[Path] = []
    for name, content in sorted(expected.items()):
        path = paths[name]
        if path.is_file() and path.read_bytes() == content.encode("utf-8"):
            continue
        changed.append(path)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            temporary.write_text(content, encoding="utf-8", newline="\n")
            temporary.replace(path)
    for name in sorted(previous - set(expected)):
        path = paths[name]
        if path.is_file():
            changed.append(path)
            if not check:
                path.unlink()
    return tuple(changed)
