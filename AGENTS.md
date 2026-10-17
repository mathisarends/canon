# Canon workspace

Read `docs/design-decisions/0001-workspace.md` for the source inventory and
`docs/migration.md` for current versus planned capabilities. `VISION.md` describes
the target; do not treat illustrative APIs as implemented interfaces.

## Boundaries

- `packages/fastapi-canon`: composition, Dishka lifecycle, HTTP contracts, optional
  integration modules. Core must import and run without either extension.
- `packages/fastapi-streams`: typed SSE, OpenAPI, Python/TypeScript client generation.
- `packages/fastapi-wsrpc`: successor `fastapi-wsrpc` / `fastapi_wsrpc`, with
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
