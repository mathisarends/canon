# Optional error-contract checking

Run the source checker to find application exceptions missing from a direct
`CanonRouter` operation's `raises=` declaration:

```console
python -m fastapi_canon.check_error_contracts src
```

Pass Python import roots: for `src/app/features/...`, use `src`, not `src/app`.
Multiple roots are accepted when they contain different modules. In this
workspace, run:

```console
uv run --locked python -m fastapi_canon.check_error_contracts examples/reference-service/src --strict
```

The checker is included in Canon and needs no extra dependencies or annotations
on application services. It parses source without importing the inspected
application, constructing a Dishka container, or opening application resources.
It is optional development tooling; normal route registration, runtime exception
mapping and OpenAPI validation keep their existing behavior.

## How the check works

The checker compares two sets for each operation: application exceptions escaping
the supported source paths, and errors declared by that operation and its router.
It reads both from source; it does not execute the application.

```mermaid
flowchart TD
    CLI["check_error_contracts src"] --> AST["Parse Python files into an AST"]
    AST --> INDEX["Resolve imports, aliases, types and definitions"]
    INDEX --> CONTRACT["Read ErrorRegistry and combine policy + router + operation raises"]
    INDEX --> CALLS["Follow endpoint, service, helper and dependency calls"]
    CALLS --> HANDLING["Remove caught exceptions and include translated exceptions"]
    HANDLING --> MATCH{"Registry mapping found through inheritance?"}
    CONTRACT --> MATCH
    MATCH -->|Yes| COMPARE{"Mapped error declared?"}
    COMPARE -->|Yes| COVERED["Supported error path covered"]
    COMPARE -->|No| MISSING["CAN001: missing raises entry"]
    MATCH -->|No| UNMAPPED["CAN002: missing registry mapping"]
    INDEX -.->|Unresolved declaration| UNKNOWN["CAN003: incomplete analysis"]
    CONTRACT -.->|Dynamic contract| UNKNOWN
    CALLS -.->|Abstract port or unresolved call| UNKNOWN
    COVERED --> REPORT["Text or JSON report + optional CI exit status"]
    MISSING --> REPORT
    UNMAPPED --> REPORT
    UNKNOWN --> REPORT
```

For example, `complete_task` calls `TaskService.complete`, which can explicitly
raise `TaskNotFound`. The checker finds its `task_not_found` registry mapping and
looks for that exact error in the operation's combined `raises`. Removing the
declaration produces `CAN001` with the call path. If the same service calls an
abstract repository method, that call also produces `CAN003`: a known gap and an
incomplete analysis can appear together.

The command is the supported entry point. The `_checks` modules, their types and
constants, and the report objects are private implementation details;
the documented JSON fields are the machine-readable interface.

## Findings and CI

Given a service method that raises `TaskNotFound`, an endpoint calling that method
must declare its mapped `task_not_found` error, either locally or on its router.
The checker reports the source location and resolved call path when it is missing:

```text
service.py:24: CAN001 [app.router.complete_task] app.service.TaskNotFound: app.errors.task_not_found is missing from raises
  app.router.complete_task -> app.service.TaskService.complete
```

| Code | Meaning |
| --- | --- |
| `CAN001` | An explicit application exception has a registry mapping that is missing from the operation's combined `raises`. |
| `CAN002` | An explicit application exception has no mapping in that router's registry. |
| `CAN003` | A declaration or execution path could not be fully analyzed. |

Default mode prints findings and exits zero. Use `--strict` to exit one for
contract gaps. Incomplete analysis remains visible and does not fail this mode.
Add `--require-complete` to fail for incomplete operations or a scan containing no
supported operations. Use both flags when both conditions should fail CI:

```console
python -m fastapi_canon.check_error_contracts src --strict --require-complete
python -m fastapi_canon.check_error_contracts src --strict --format json
```

Invalid roots, duplicate module names, unreadable files and syntax errors exit
two. JSON output includes each operation's diagnostics, a `complete` flag,
`contract_gaps` and `incomplete_operations`. An operation can be fully analyzed
and still contain a contract gap. An empty result does not establish coverage.

When an error catalog or `raises` sequence cannot be resolved, the checker reports
incomplete analysis instead of guessing which errors are missing.

## Supported source patterns

The initial checker follows direct `CanonRouter` declarations with ordinary route
decorators, including `api_route`. It reads literal `ErrorRegistry(errors=[...])`
and named `Error` definitions. A direct, statically resolved `RouterPolicy` supplies
its registry, dependencies and shared errors. Policy, router and operation `raises`
combine; supported
sequences include named lists/tuples, unpacking and concatenation. Router contracts
do not propagate to separately included child routers.

Analysis follows imports, aliases and explicit re-exports within the supplied
roots; typed service methods, including `FromDishka[Service]`; direct helper
calls; simple constructor-injected `self` attributes; and annotated return values.
It also follows function dependencies declared with `Depends` or `Security`,
including `Annotated` aliases, nested dependencies and router/operation dependency
lists. Dependencies supplied later while mounting an application are outside this
source-declaration check.

Explicit `raise` statements propagate through supported function calls and simple
branches. `try`/`except` removes caught exceptions, preserves bare re-raises and
includes translated exceptions from handlers. Exception matching and registry
selection follow statically resolvable Python inheritance order, so a more
specific registered error takes precedence over a base mapping. Conditions are
not proved feasible: a finding describes a possible source path, not a guarantee
that a particular request reaches it.

## Analysis boundaries

`complete` describes analysis of the supported explicit source paths, not proof
that no other runtime exception can occur. The checker does not model implicit
interpreter errors, every Python protocol or implicit descriptor invocation,
framework internals, application startup, transactions or background tasks.
Explicit built-in exceptions are outside the application-error comparison.

Unresolved calls, abstract ports, external constructors, custom decorators,
recursive calls, dynamic contracts, nested route factories, deferred coroutine
execution and unsupported control flow produce `CAN003`. Loops, context managers,
comprehensions, `match` and `except*` are currently outside the supported flow
analysis. Reassigned module declarations and detected contract mutations also
prevent a complete result. Dishka provider bindings are not executed or inferred:
an abstract port remains incomplete even if the application always binds one
implementation.

Only source route declarations are inspected; the tool does not establish which
routers are actually mounted, follow `dependency_overrides`, or validate composed
registries from other features. Pass all relevant source roots, retain runtime
contract validation and test the application's intended error paths.

When the scanned source contains `Composition(router_policy=...)`, the checker
marks operations incomplete and suppresses guessed contract gaps: determining
which operations inherit that policy requires analyzing application mounting.

Plain FastAPI routers are skipped. Canon's SSE and WebRTC declarations are outside
this first version. Generator bodies are explicitly incomplete: failures after
response start need transport-specific error events or protocol handling, rather
than additional HTTP `raises` entries.
