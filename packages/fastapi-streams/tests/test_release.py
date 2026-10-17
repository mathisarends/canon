import subprocess
from pathlib import Path

import pytest

from scripts.check_release import check_release


@pytest.fixture
def release_repo(tmp_path: Path) -> Path:
    (tmp_path / "fastapi_streams").mkdir()
    _write_versions(tmp_path, "0.2.0")
    _git(tmp_path, "init", "--initial-branch=main")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "Release candidate")
    _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
    return tmp_path


@pytest.mark.parametrize("version", ["0.2.0", "1.0.0a1", "1.0.0b2", "1.0.0rc1"])
def test_release_accepts_matching_versions_on_main(release_repo: Path, version: str):
    _write_versions(release_repo, version)
    assert check_release(f"v{version}", release_repo) == version


@pytest.mark.parametrize(
    "tag",
    [
        "0.2.0",
        "v0.2",
        "v00.2.0",
        "v0.2.0rc01",
        "v0.2.0+local",
        "v0.2.0.dev1",
        "v0.2.0.post1",
        "v0.2.0\n",
        "v0.2.0;echo unsafe",
    ],
)
def test_release_rejects_unsupported_tags(release_repo: Path, tag: str):
    with pytest.raises(ValueError, match="Use vX.Y.Z"):
        check_release(tag, release_repo)


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("pyproject.toml", "pyproject.toml"),
        ("fastapi_streams/__init__.py", "__version__"),
        ("uv.lock", "uv.lock"),
    ],
)
def test_release_rejects_mismatched_versions(
    release_repo: Path, path: str, message: str
):
    source = release_repo / path
    source.write_text(source.read_text().replace("0.2.0", "0.1.0"))
    with pytest.raises(ValueError, match=message):
        check_release("v0.2.0", release_repo)


def test_release_rejects_commit_outside_main(release_repo: Path):
    _git(release_repo, "checkout", "-b", "unmerged")
    (release_repo / "unmerged.txt").write_text("unreviewed change")
    _git(release_repo, "add", ".")
    _git(release_repo, "commit", "-m", "Unmerged change")
    with pytest.raises(ValueError, match="must be on origin/main"):
        check_release("v0.2.0", release_repo)


def test_release_rejects_missing_main_ref(release_repo: Path):
    _git(release_repo, "update-ref", "-d", "refs/remotes/origin/main")
    with pytest.raises(ValueError, match="must be on origin/main"):
        check_release("v0.2.0", release_repo)


def test_release_accepts_older_commit_on_main(release_repo: Path):
    candidate = _git(release_repo, "rev-parse", "HEAD")
    (release_repo / "later.txt").write_text("later change on main")
    _git(release_repo, "add", ".")
    _git(release_repo, "commit", "-m", "Later change")
    _git(release_repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(release_repo, "checkout", "--detach", candidate)
    assert check_release("v0.2.0", release_repo) == "0.2.0"


def test_release_does_not_import_package(release_repo: Path):
    source = release_repo / "fastapi_streams/__init__.py"
    source.write_text('__version__ = "0.2.0"\nraise RuntimeError("must not execute")\n')
    assert check_release("v0.2.0", release_repo) == "0.2.0"


def _write_versions(root: Path, version: str) -> None:
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "fastapi-streams"\nversion = "{version}"\n'
    )
    (root / "fastapi_streams/__init__.py").write_text(f'__version__ = "{version}"\n')
    (root / "uv.lock").write_text(
        f'[[package]]\nname = "fastapi-streams"\nversion = "{version}"\n'
    )


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Release test",
            "-c",
            "user.email=release@example.test",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
