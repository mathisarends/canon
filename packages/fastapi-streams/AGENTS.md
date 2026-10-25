# Repository guidance

`fastapi-streams` turns typed FastAPI SSE generators into an OpenAPI 3.2 contract
and generated TypeScript/Python clients. Follow the workspace rules in the root
`AGENTS.md`; this file adds package-specific conventions.

## Layout

- `fastapi_streams/router.py`: `StreamRouter` and endpoint validation.
- `fastapi_streams/codegen/`: export (`openapi.py`), shared HTTP IR (`ir.py`),
  emitters (`python.py`, `typescript.py`), CLI (`cli.py`) and diagnostics.
- `fastapi_streams/codegen/templates/`: generated runtimes. `python/runtime.py`
  and `sse.ts` are copied verbatim into every generated SDK.
- `examples/agent_runs/` and `tests/fixtures/` contain committed generated SDKs.

## Commands

Run from the workspace root after `uv sync --locked --all-packages --all-groups`
and `npm ci --ignore-scripts --prefix packages/fastapi-streams`:

```console
uv run --locked --directory packages/fastapi-streams python -m pytest -q
uv run --locked --directory packages/fastapi-streams python scripts/codegen.py
uv run --locked --directory packages/fastapi-streams python scripts/codegen.py --check
npm run --prefix packages/fastapi-streams test
npm run --prefix packages/fastapi-streams typecheck
uv run --locked python scripts/check.py lint
```

Use `python -m pytest`, not bare `pytest`: tests import the `tests` package from
the package directory.

## Python module layout

In new or edited Python source modules, put the public API (public classes and
functions) first, immediately after imports and module constants. Define private
implementation helpers below the public API. Keep the executable `__main__`
entrypoint at the end of the module.

## Generated clients

Generated client files are owned by the generators; update their templates rather
than editing generated output by hand. After a template change, run
`scripts/codegen.py` to regenerate every committed SDK and its manifest, then run
the Python and TypeScript tests. Runtime changes that alter generated code need a
changelog entry telling consumers to regenerate.
