# Releasing

[Documentation](README.md) · [Project](../README.md)

A pushed Git tag is the release signal. The agent preparing a release only needs
permission to push the release tag to GitHub. GitHub Actions authenticates to PyPI
with OIDC (Trusted Publishing); no PyPI password or API token is stored in GitHub
or provided to an agent.

## One-time maintainer setup (required before the first tag)

### 1. Configure the GitHub environment

Open [Settings → Environments](https://github.com/mathisarends/fastapi-streams/settings/environments)
and create an environment named **`pypi`**.

- Under **Deployment branches and tags**, select **Selected branches and tags**
  and add a **tag** rule for `v*`. Do not add a branch rule.
- Recommended: add a required reviewer if you want a human to approve each PyPI
  upload after the agent pushes a tag. Enable prevention of self-review if your
  approval policy requires another person. Without required reviewers, a valid
  tag publishes automatically after validation and tests pass.
- Do not add a PyPI secret. The `publish` job requests `id-token: write`; the
  separate GitHub Release job requests `contents: write` for its built-in
  `GITHUB_TOKEN`. Repository or organization policies must allow these permissions
  and the actions referenced in the workflows.

Create and protect this environment explicitly before publishing; a workflow can
otherwise create an environment without your intended protection rules.

### 2. Register the PyPI Trusted Publisher

Sign in to PyPI with the account that owns (or will own) `fastapi-streams`.
For an existing project, open its
[Publishing settings](https://pypi.org/manage/project/fastapi-streams/settings/publishing/).
For a first publication, use
[Add a new pending publisher](https://pypi.org/manage/account/publishing/).

Select **GitHub** and enter these exact values:

| Field | Value |
| --- | --- |
| PyPI project name (pending publishers only) | `fastapi-streams` |
| Owner | `mathisarends` |
| Repository name | `fastapi-streams` |
| Workflow name | `release.yml` (filename only) |
| Environment name | `pypi` |

Confirm you control the package name. A pending publisher does not reserve a name;
the project is created on the first successful upload. PyPI and TestPyPI have
independent accounts and publisher registrations; this workflow publishes to
production PyPI only.

### 3. Protect the release inputs

In [Settings → Rules → Rulesets](https://github.com/mathisarends/fastapi-streams/settings/rules),
protect `main` with pull request reviews and the existing CI and compatibility
checks. Review changes to the workflows, packaging configuration, and release
scripts as carefully as library changes.

Create a tag ruleset targeting `v*`. Restrict creation to authorized release
maintainers or a dedicated release GitHub App, and prevent updates and deletion.
Configure bypass access deliberately so the actor pushing a release tag can
create it. An agent that only prepares release PRs does not need tag creation
permission. An agent authorized to trigger releases does need that GitHub
permission, but still needs no PyPI credentials.

## Prepare and trigger a release

1. Resolve known release blockers and decide which changes belong in this version.
2. Prepare a PR against `main`. Update `project.version` in `pyproject.toml` and
   `__version__` in `fastapi_streams/__init__.py`, then run `uv lock` and commit the
   updated `uv.lock`. Keep all three versions identical. For the first `0.0.1`
   release these files already agree; a version bump is only needed for a new
   version. Describe user-facing changes in the PR; GitHub uses merged PRs to
   generate release notes.
3. Merge after review and passing checks. Then tag the intended commit on `main`:

   ```sh
   git fetch origin main --tags
   git switch main
   git pull --ff-only origin main
   python scripts/check_release.py v0.0.1
   git tag -a v0.0.1 -m "Release v0.0.1"
   git push origin v0.0.1
   ```

   Substitute the intended version everywhere. For an older release candidate
   already on `main`, check out that exact commit before validating and tagging.
   An annotated tag is recommended; do not move or reuse a published tag.

4. Follow the [Release workflow](https://github.com/mathisarends/fastapi-streams/actions/workflows/release.yml)
   and approve the `pypi` deployment if required reviewers are configured.
5. Verify the version on [PyPI](https://pypi.org/project/fastapi-streams/) and the
   [GitHub Releases page](https://github.com/mathisarends/fastapi-streams/releases).
   Consumers can then install `fastapi-streams[codegen]==0.0.1` from PyPI.

Supported tags are `vX.Y.Z`, `vX.Y.ZaN`, `vX.Y.ZbN`, and `vX.Y.ZrcN`, using
canonical numbers without leading zeroes. Prereleases are published to PyPI and
marked as prereleases on GitHub. Development, local, and post-release versions
are deliberately rejected.

If a GitHub Actions agent pushes the tag, use an appropriately scoped GitHub App
installation token or personal access token. Events caused by the repository's
default `GITHUB_TOKEN` do not normally start another workflow. A locally running
agent can use its authorized GitHub Git credentials. Neither approach requires
PyPI credentials.

## What the workflow guarantees

`.github/workflows/release.yml` runs these stages in order:

1. **Validate:** reject unsupported tags, mismatched versions in the project,
   module or lockfile, and commits outside `origin/main`. Validation reads the
   module with Python's AST parser instead of importing package code.
2. **Test:** call the existing CI workflow (Python 3.12–3.14, lint, types, Python
   and TypeScript coverage, generated-file drift and wheel smoke tests) and the
   complete Linux/Windows dependency compatibility matrix. These run against the
   tag's exact commit and must all pass.
3. **Build:** check the lockfile, build an sdist and a wheel from it, check metadata
   and the README with Twine, then smoke-test this wheel in isolated environments
   for the core install and each Python HTTP backend. Upload the distributions as
   one immutable workflow artifact.
4. **Publish:** download that artifact in a fresh job, pass the `pypi` environment
   restrictions, and publish through PyPI Trusted Publishing with attestations.
   This job has no source checkout, build steps, or stored credentials. Only this
   job can request an OIDC token.
5. **GitHub Release:** after PyPI succeeds, attach the same wheel and sdist to a
   GitHub Release with automatically generated release notes. Only this job has
   repository write permission.

Runs for the same tag are serialized without canceling an in-progress release.
All external actions in the release and its called workflows are pinned to full
commit SHAs; review and update those pins when adopting action updates.

## Failures and retries

- Validation, test or build failure: nothing is published. Fix the release inputs
  through a PR and use a new version/tag for the corrected candidate.
- Missing publisher or environment approval: complete the setup above and rerun
  **failed jobs** on the original workflow run. This preserves the tested build
  artifact. Artifacts are retained for 30 days.
- PyPI succeeded but GitHub Release creation failed: rerun only the failed GitHub
  Release job. Do not rerun successful publishing jobs or rebuild the same PyPI
  version. If a GitHub Release already exists after a partial failure, inspect it
  and attach the original run's missing assets manually.
- Partial PyPI upload: inspect which files reached PyPI before retrying. The
  workflow deliberately does not skip existing files; PyPI does not allow replacing
  a published distribution. Publish a new version for changed package contents.

The setup is implemented here without creating a tag or publishing a package.
The first live upload also verifies your external PyPI and environment settings.

## References

- [PyPI: publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [PyPI: creating a project with a pending publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [PyPI: security model](https://docs.pypi.org/trusted-publishers/security-model/)
- [GitHub: OIDC with PyPI](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi)
- [GitHub: triggering workflows from workflows](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow)
