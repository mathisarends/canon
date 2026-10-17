# Canon workspace

Read `docs/design-decisions/0001-workspace.md` for the source inventory and
`docs/migration.md` for current versus planned capabilities. `VISION.md` describes
the target; do not treat illustrative APIs as implemented interfaces.
Use `TODO.md` for the prioritized next work block and release setup still required.
Write all repository Markdown documentation in English, including TODO lists,
changelogs, guides, and agent instructions.

## Boundaries

- `packages/fastapi-canon`: composition, Dishka lifecycle, HTTP contracts, optional
  integration modules. Core must import and run without either extension.
- `packages/fastapi-streams`: typed SSE, OpenAPI, Python/TypeScript client generation.
- `packages/fastapi-rpckit`: successor `fastapi-rpckit` / `fastapi_rpckit`, with
  FastAPI as a required dependency. Preserve wire behavior and client contracts.
- Extensions must not acquire a required dependency on Canon or each other.
- Keep independent package versions. Do not add a shared core without concrete reuse.
- Application code follows `guides/architecture.md`: feature slices, inward
  dependencies, framework-free domain, Dishka for application dependencies.

## Workflow

Use the root environment and lockfile:

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
```

`check.py` also accepts `lint`, `types`, `test`, and `clients`. It runs each
package with its own configuration and working directory. Do not combine all
package suites into one pytest process: their `tests`/`examples` modules collide.
Use `uv run --locked --directory packages/<member> pytest ...` for focused work.

Keep one root `uv.lock`. Preserve package-specific type/lint settings. Generated
clients are changed through generators/templates, then checked for drift.
Build/install checks must use actual artifacts in fresh environments, independent
of workspace source overrides. Do not publish or archive repositories as part of
routine development. The nested imported `.github` directories are historical
configuration; only root workflows execute for this repository.

## Release preparation

Read `docs/releases.md` for prepared versions, publication order, publisher setup
and the release workflow. `docs/compatibility.md` records tested dependency
combinations; `docs/rpc-parity.md` records the predecessor comparison and consumer
migration limits. Do not treat prepared source versions as published releases.

Run the standalone minimum-dependency smoke matrix with
`uv run --locked python scripts/check_distributions.py --python 3.12 --dependencies minimum`.
The default mode checks current compatible dependencies. Both modes create fresh
wheel environments and write dependency inventories under `dist/`. Check Streams'
installed CLI/backends with `uv run --locked python scripts/check_streams_artifacts.py`.
For an external RPC contract, follow the installed-wheel command in the parity
report; SDK compilation alone does not establish a full application migration.

Use `release.toml` and `scripts/release.py` for package/tag/version metadata.
Prepare source versions and pins, regenerate clients, pass checks and commit/merge
to `main`. Wait for CI on that exact commit, then dispatch `release.yml` with
`dry_run=true` for the selected package/version. Before a real publication,
finalize the changelog date and pass CI for the final source. Only dispatch with
`dry_run=false` when explicitly authorized to publish. Publish Streams before a
Canon version that pins it. Verify public-index installs and release/tag results.
On failure, follow the documented resume procedure with the original run's
verified artifacts; do not replace published contents or move existing tags.
