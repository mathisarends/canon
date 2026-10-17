# Contributing

Use Python 3.12–3.14, uv 0.9.2 or newer, and Node.js 24 for the TypeScript tests.
Run these commands at the repository root:

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
```

The first command installs all members and their development groups into the
root `.venv`. The reference service is a development member, not a fourth
published stack library. Keep only the root `uv.lock`; `uv lock` updates it.

Run one gate with `check.py lint`, `types`, `test`, or `clients`. Package suites
run in separate processes to keep their `tests` and `examples` imports isolated.
Use `uv run --locked --directory packages/fastapi-canon pytest -q` for one suite.
Run `uv run --locked pytest -q` for the workspace integration suite only.

Package-level Ruff, Mypy, Pyright, and coverage settings remain authoritative.
The root runner coordinates them instead of imposing one setting on generated
clients and every protocol. RPC's TypeScript tests use npx for TypeScript and
Prettier; the first run may download those tools. Streams has a committed npm
lockfile. Both client generators remain owned by their respective package.

`check_distributions.py` builds wheels and sdists for each library and installs
the wheels in six fresh environments, without uv workspace overrides. It checks
standalone imports, absent optional packages, CLIs, typed markers, HTTP, SSE,
RPC, and the shared Dishka lifecycle. Build outputs live in ignored `dist/`.

Run the composed example with:

```console
uv run --locked uvicorn examples.stack_service:app --reload
```

`POST /counter` increments application state, `GET /counter/events` emits its
current typed SSE value, and `/rpc` accepts `counter.increment`. The example
demonstrates composition and scopes; it has no persistence or authentication.
The larger [reference service](../examples/reference-service) demonstrates
feature slices, authentication, persistence, and transactions. Its local Feature
descriptor predates the Canon library and remains a documented migration item.

Imported nested `.github` directories and release scripts are retained as
historical references. They are not executable workflows in this repository.
Only root workflows define current CI; publishing remains disabled until the
new release policy is implemented.
