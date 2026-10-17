# Development

[Documentation](README.md) · [Project](../README.md)

## Run the checks

```sh
uv sync --all-extras
npm ci
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pylint fastapi_streams
uv run pre-commit run --all-files
npm run typecheck
npm run test:coverage
uv run pytest -q --cov --cov-report=term-missing --cov-report=xml:coverage-python.xml
uv run python scripts/codegen.py --check
uv build
uv run --frozen twine check --strict dist/*
uv run python scripts/check_package.py
```

Run `uv run python scripts/codegen.py` to regenerate all committed examples and
test fixtures. The tests cover real FastAPI-to-Node and FastAPI-to-Python HTTP
requests, strict narrowing, recursive models, authentication, disconnect
cleanup, fragmented parsing, cancellation and drift detection. Install Node
dependencies before pytest to enable its TypeScript acceptance test. CI does
this and checks Python 3.12, 3.13 and 3.14. Generated Python is checked by Pyright
and behavior tests; its generator owns formatting. Run `uv run pre-commit install`
once to enable the same checks before local commits. Hooks use tools from `uv.lock`;
Ruff checks style and formatting, Pyright checks types, and Pylint checks errors and
warnings. CI also executes the complete hook configuration.

## Dependency compatibility

The locked CI job runs on Python 3.12, 3.13 and 3.14. A separate compatibility matrix
tests all three interpreters on Linux and Windows, each with `lowest` and `latest`
dependencies (12 combinations). It runs on pushes, pull requests, manual dispatch
and every Monday. Each run records resolved versions and JUnit results as artifacts.

Run an individual matrix case locally with:

```sh
uv run python scripts/test_compat.py --python 3.12 --dependencies lowest
uv run python scripts/test_compat.py --python 3.14 --dependencies latest
```

The script creates an isolated environment under `.pytest_cache/compat-env`, resolves
the published FastAPI, Pydantic, HTTPX, HTTPX2 and codegen bounds independently of `uv.lock`,
and runs the complete behavioral suite. Test tooling stays current. The lowest
profile uses the oldest compatible binaries of the direct dependencies; on Python 3.14 this
currently selects Pydantic 2.12.0. Python 3.12/3.13 test the declared 2.11.2 minimum.
Pydantic 2.11.0/2.11.1 lose the discriminator in named union schemas, so they are
excluded by the package metadata.

Integration tests start a real Uvicorn server, export the installed FastAPI version's
contract and generate both SDKs afresh. They check GET/POST, authentication, request
validation, query/header values, custom success status, immediate event delivery,
consumer cancellation and server/dependency cleanup. Node, HTTPX and HTTPX2 consume
streams that stay open until the client disconnects. Every compatibility case tests
both Python HTTP libraries, generating a separate SDK for each.

Committed OpenAPI fixtures live in `tests/fixtures/*.openapi.json`. Only the locked
job checks their exact snapshots; compatibility jobs generate fresh contracts and
clients instead of comparing version-dependent schema formatting.

## Coverage and package checks

Python reports include branch coverage for the library and the executed generated
example transport, with an 85% combined floor. Identical runtime copies in the
fixtures are checked for drift rather than counted twice. TypeScript's generated
example transport has floors of 95% lines, 90% branches and 90% functions. CI uploads
the Python XML and TypeScript LCOV reports for each locked interpreter.

The schema matrix validates accepted/rejected payloads and runs strict TypeScript
and Python type checks on newly generated packages, including both HTTP backends.
Consumer type tests also assert
that missing arguments, wrong parameter types and invalid event fields are rejected.
Contract boundary tests cover unsupported serialization, references and collisions.

Package checks install the freshly built wheel in three new environments: core
only, codegen with HTTPX only, and codegen with HTTPX2 only. They bypass cached local
wheels so repeated builds of the same release version test the current artifact.
In a directory
outside the checkout they invoke the installed `fastapi-streams` command, exercise
`schema`, `generate`, `check` and drift exit codes, compile the generated TypeScript
and consume an event through the generated Python SDK. Metadata and `__version__`
must match the release version in `pyproject.toml`.

## Supported scope and roadmap

GET/POST JSON SSE data; scalar path and header parameters; scalar/array query parameters;
JSON bodies; local component references; nested objects, maps, arrays, string
enums and discriminated unions. Query form arrays support both `explode` values.
Python `allOf` supports compatible object intersections. TypeScript does not
express validation constraints such as numeric ranges as refinement types.
Schema references may carry metadata (for example `description`, `title` and
`default`), but semantic siblings such as `enum`, `const`, `required`,
`additionalProperties` or `type` are rejected. Define a standalone schema with
the full restrictions; reference-chain constraints are checked before generation.
Required object keys absent from `properties` inherit the `additionalProperties`
value type (unrestricted when omitted or true). They remain required in both
SDKs. A required undeclared key combined with `additionalProperties: false` is
rejected as an unsatisfiable contract before any client files are written.

Header arrays (Fetch combines repeated headers), external references, cookies,
deepObject/matrix/label styles, multipart bodies,
tuple schemas and object/array enum values are rejected. No REST SDK replacement,
WebSockets, JSON-RPC, persistence, automatic reconnect or replay.

Next: NDJSON, then explicit event IDs, Last-Event-ID and opt-in reconnect/replay
policies. Both shipped generators already share a transport-independent HTTP IR.
