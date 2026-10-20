# Contributing

Use Python 3.12–3.14, uv 0.9.2 or newer, and Node.js 24 for the TypeScript tests.
Run these commands at the repository root:

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
npm ci --ignore-scripts --prefix packages/fastapi-webrtc
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
```

The first command installs all members and their development groups into the
root `.venv`. The reference service is a development member, not a fourth
published stack library. Keep only the root `uv.lock`; `uv lock` updates it.
Optionally run `uv run --locked pre-commit install` from the root to install the
shared lint hook. Do not install the imported package-local hook configurations.

Run one gate with `check.py lint`, `types`, `test`, or `clients`. `check.py browser`
runs WebRTC sessions in Chromium against the aiortc engine; install the browser
once with `npx playwright install chromium` in `packages/fastapi-webrtc`. It is
not part of `all` and runs as its own CI step. Package suites
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
It also builds the development-only reference service and runs its HTTP suite
against an installed Canon wheel in a seventh clean environment without either
transport extension.
Then run `uv run --locked python scripts/check_streams_artifacts.py` to check
the Streams wheel with no codegen extra and each supported Python HTTP client.
`uv run --locked python scripts/check_webrtc_artifacts.py` installs the WebRTC
wheel, regenerates the practice contract and browser client with the installed
CLI, checks them for drift and compiles the client with WebRTC's pinned
TypeScript (`npm ci --ignore-scripts --prefix packages/fastapi-webrtc` first).
The artifact scripts also generate and exercise clients from installed contracts.

Run the composed example with:

```console
uv run --locked uvicorn examples.stack_service:app --reload
```

`POST /counter` increments application state, `GET /counter/events` emits its
current typed SSE value, and `/rpc` accepts `counter.increment`. The example
demonstrates composition and scopes; it has no persistence or authentication.
The larger [reference service](../examples/reference-service) uses Canon's actual
`Feature`/`Composition` API for feature slices, authentication, persistence,
transactions, and typed HTTP errors. Its runtime and OpenAPI tests exercise that
composition with the installed Canon distribution as well as in the workspace.

Imported nested `.github` directories and release scripts are retained as
historical references. They are not executable workflows in this repository.
Only root workflows define current CI; publishing remains disabled until the
new release policy is implemented.
