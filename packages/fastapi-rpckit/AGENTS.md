# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

`fastapi_rpckit` is a Python library with distribution name `fastapi-rpckit`
(initial successor version 0.1.0). It turns
decorated channel functions and mounted service endpoints into a JSON-RPC 2.0
protocol: definition (`channel.py`, `protocol.py`), serving (`service.py`,
`runtime.py`, `dispatch.py`, `server.py`), contract generation (`schema/`), and
client generation (`codegen/`). Generated Python clients embed their runtime
from the templates under `codegen/templates/python/runtime/`.

## Environment

- Dependency management: [uv](https://docs.astral.sh/uv/)
- Supported Python versions: 3.12–3.14
- Install dependencies: `uv sync --all-groups`

## Workflow

- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Tests: `uv run pytest`
- Install pre-commit only from the workspace root using its root configuration.

## Conventions

- Library code lives in `fastapi_rpckit/`; the public API is re-exported from `fastapi_rpckit/__init__.py`.
- Use relative imports for all public re-exports in `fastapi_rpckit/__init__.py`.
- No module-level docstrings. Document a class or function only where the name is not enough.
- During consolidation preserve the existing runtime and adapter behavior. The
  successor direction is FastAPI-first; see the root README.md. Do not remove
  test seams or redesign the public API as part of a workspace move.
- Generators read the OpenRPC document, never the `RpcProtocol` object, so a new target
  language only needs an emitter beside `codegen/python.py` on top of `codegen/ir.py`.
- Generated code must pass `ruff check` and `ruff format` in the consuming repository.
- Tests live in `tests/` and mirror the package structure.
- Keep `pyproject.toml` as the single source of truth for metadata and tool config.
- Before 1.0, any breaking change requires the next minor version with patch zero
  (`0.x.y` to `0.(x+1).0`), including signature or validation changes without wire
  changes. Follow the root release policy and record migration steps in the
  changelog under `### Breaking changes`.

- Use the current intended API only. Remove superseded APIs, compatibility aliases,
  deprecated wrappers, and parallel legacy implementations instead of preserving
  them. Document breaking changes and concrete migration steps in `CHANGELOG.md`,
  update guides/tests, and regenerate clients. This applies throughout the project.
