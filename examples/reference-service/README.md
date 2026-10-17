# Reference service

A small task API demonstrating feature slices, repositories, mapping, transactions,
and authentication with the real `fastapi-canon` library. Features contribute
providers, `CanonRouter` declarations, and typed error registries. `Composition`
owns the Dishka container and its shutdown; the application has no local Feature
implementation or second container/lifespan manager.

The example defaults to SQLite for convenient local use. Persistent schemas should use Alembic; `create_schema.py` exists only to bootstrap this disposable example. See [Database migrations](../../guides/migrations.md) for the preferred layout.

```console
uv sync --locked --all-packages --all-groups
uv run python create_schema.py
uv run uvicorn app.main:app --reload
```

The task API is available under `/api/v1/tasks`; interactive documentation is at `/docs`. Task routes require `Authorization: Bearer local-development-token`. This token is a local example default only; deployed services inject real authentication configuration and a production `TokenVerifier` adapter.

Run the commands above from `examples/reference-service`. From the repository
root, use `uv run --locked --directory examples/reference-service pytest -q` for
the HTTP/authentication/contract regressions.

Errors now use Canon's RFC 9457 `application/problem+json` contracts. The stable
codes are `authentication_required`, `task_not_found`, and
`request_validation_error`; `WWW-Authenticate: Bearer` is preserved for 401.
Successful response schemas, paths, and operation IDs remain unchanged. The
versioned feature routes and the public `/health` endpoint are wired explicitly
at the composition root.
