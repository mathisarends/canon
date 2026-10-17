# Canon — Vision for the FastAPI Application Stack

> **One coherent way to build production-grade FastAPI applications — from architecture and HTTP contracts to typed streaming and realtime RPC.**

**Status:** Proposed direction / living vision  
**Date:** 2026-10-17  
**Repository:** `mathisarends/fastapi-canon` (proposed monorepo)  
**Audience:** Maintainers, contributors, application developers, and coding agents

---

## 1. The idea

FastAPI makes it easy to build an endpoint. The harder question is how to build a large application that remains consistent as its features, transports, contracts, clients, and contributors multiply.

Canon answers that question with a coherent, opinionated application stack. It combines documented architecture conventions with focused, interoperable Python libraries for three communication models:

1. **HTTP request/response:** Feature composition, dependency injection, API conventions, typed success and error contracts.
2. **HTTP streaming:** Typed server-sent events (SSE), OpenAPI stream contracts, and generated clients.
3. **Bidirectional WebSocket RPC:** Typed methods, notifications, subscriptions, binary/raw channels, contracts, and generated clients.

The purpose is not to replace FastAPI, invent another general-purpose framework, or hide the underlying platform. The purpose is to make the patterns that repeatedly work in production explicit, enforceable, and easy to reuse.

Canon is both **a set of conventions** and **a set of capabilities**. An application may adopt the architecture guides alone, install one package, or use all three together. Regardless of adoption level, the development model should feel coherent.

**Positioning:** *FastAPI is the foundation. Canon is the architecture and composition layer. Streams and RPC are focused extensions.*

## 2. The problem we are solving

A typical application eventually accumulates several disconnected answers to the same questions:

- How are features structured, composed, and tested?
- How are dependencies and their lifecycles managed across request, connection, and application scopes?
- How do exceptions become stable, typed public API errors?
- Where does the contract for a streaming endpoint live?
- How does a frontend know which SSE events or RPC methods exist?
- How are clients regenerated without drifting from the server?
- How do HTTP, SSE, and WebSocket features coexist in one application?
- How can a coding agent implement a new feature without inventing a different architecture each time?

Independent libraries solve pieces of these problems. But three unrelated packages can also drift: incompatible dependencies, competing router conventions, duplicate schema code, inconsistent error handling, and subtly different lifecycle semantics.

Canon treats the **application as the unit of coherence**, without making the whole ecosystem one indivisible Python distribution.

## 3. Product model

### 3.1 One ecosystem, three independently installable packages

| Distribution | Python import | Responsibility |
| --- | --- | --- |
| `fastapi-canon` | `fastapi_canon` | Feature composition, Dishka-based DI, HTTP router conventions, success/error contracts, lifecycle integration, and architectural guidance. |
| `fastapi-streams` | `fastapi_streams` | Typed HTTP/SSE streams, OpenAPI stream descriptions, and Python/TypeScript stream SDK generation. |
| **WebSocket RPC package — name TBD** | **Import path TBD** | FastAPI-native typed WebSocket RPC, OpenRPC contracts, subscriptions, bidirectional methods, binary/raw sockets, and Python/TypeScript SDK generation. |

The RPC component is the successor to `pyrpckit`, not a permanent second branch of that project. Its design becomes explicitly FastAPI-first; the existing RPC engine, contract logic, and tests are assets to preserve, not abstractions to rewrite reflexively.

**Naming constraint:** `fastapi-wsrpc` is a useful architectural working label but **not an available PyPI distribution name**: packaging normalization treats it as equivalent to the already-published `fastapi-ws-rpc`. Select and verify a distinct final distribution name before creating the release workflow. `fastapi-rpckit` is a candidate, **not a decided or availability-verified name**.

### 3.2 Canon as the umbrella identity

**Canon** is the name of the approach and ecosystem. `fastapi-canon` is the public monorepo and the name of its application-composition package. The two meanings should be explained explicitly in the README and docs to avoid ambiguity.

- **Umbrella:** Canon — the opinionated FastAPI application stack.
- **Core package:** `fastapi-canon` — feature composition and HTTP contracts.
- **Capabilities:** Streams and WebSocket RPC — separately installable, integrated but independently useful.
- **Documentation:** Architecture guides, reference service, compatibility policy, and agent instructions are first-class deliverables.

Avoid a premature rename of working packages solely for visual uniformity. A shared conceptual model, not matching import prefixes, creates the real developer experience.

## 4. Principles

### 4.1 FastAPI-native, not FastAPI-adjacent

Prefer familiar `FastAPI`, `APIRouter`, Pydantic models, route decorators, dependencies, middleware, and lifespan semantics. A Canon user should recognize an ordinary FastAPI application.

New abstractions must remove a recurring problem or express a contract FastAPI does not already express sufficiently. Do not introduce wrappers merely to make the stack look proprietary.

### 4.2 Opinionated at architectural boundaries; pragmatic inside features

Encourage feature slices and inward-pointing dependencies. Use `domain`, `application`, `infrastructure`, and `presentation` where responsibilities justify them; do not mechanically force four directories on trivial features.

The domain must remain independent of FastAPI, Pydantic, Dishka, SQLAlchemy, and transport details. Use Dishka as the deliberate application-level DI convention. Keep FastAPI `Depends` for HTTP and WebSocket boundary concerns.

### 4.3 One source of truth per contract

Declare API operations, payload types, event variants, and documented errors in Python. Generate machine-readable contracts and SDKs. Avoid handwritten client mirrors.

- HTTP success/error contracts: OpenAPI and RFC 9457 Problem Details, with stable error codes.
- SSE: OpenAPI streaming descriptions, typed event unions, and generated async iterators.
- RPC: OpenRPC (and explicit RPC protocol metadata where needed), typed methods/events/streams, and generated clients.

There is **no requirement** to force OpenRPC into OpenAPI or represent different protocols as if they had identical semantics.

### 4.4 Independent use, integrated experience

Each published package should work outside the full Canon stack within its documented scope. The Canon core may provide *optional* adapters for streams and RPC. Streams and RPC must not import Canon as a hard dependency.

Cross-package integration must be tested as carefully as any public API.

### 4.5 Small public surfaces, strong internals

Prefer a clear, stable entry point over exposing every runtime primitive. Keep dispatch, connection management, framing, validation, backpressure, and codegen internals modular and testable, but expose only what real users need.

### 4.6 Coding agents are primary consumers

Guides must be concise, normative, and executable through a reference application. They should tell an agent **what to do, why it is the standard, and how to verify it**. Examples are part of the specification; inconsistent examples are defects.

## 5. Responsibility boundaries

### 5.1 `fastapi-canon`: application composition and HTTP contracts

Canon owns:

- Feature descriptors and explicit composition at the application root.
- Ordered registration of routers, Dishka providers, error registries, exception handlers, and lifespan contributions.
- `CanonRouter` and its HTTP success/error contract conventions.
- Shared typed Problem Details behavior and OpenAPI representations.
- The canonical application-level dependency injection and lifecycle model.
- Optional integration entry points, such as `fastapi_canon.integrations.streams` and `fastapi_canon.integrations.rpc`.
- Architecture guides, reference applications, and cross-package contract tests.

Canon does **not** own SSE framing, SSE code generation, JSON-RPC dispatch, or WebSocket wire protocols.

### 5.2 `fastapi-streams`: typed HTTP streaming

Streams owns:

- `StreamRouter` (or equivalent FastAPI-native endpoint declaration) with typed stream results.
- Event models, discriminated unions, SSE framing semantics, cancellation, and connection cleanup.
- OpenAPI stream export and validation.
- Python and TypeScript client generation for supported streaming operations.
- Stream-specific contract fixtures, runtime tests, and CLI commands.

It must remain usable with a plain `FastAPI()` application. It does not need to import or require Canon.

### 5.3 WebSocket RPC successor: bidirectional realtime contracts

The successor to `pyrpckit` owns:

- Typed request/response methods, notifications, subscriptions, and server-to-client calls.
- Channels or namespaces that group operations by application capability.
- WebSocket connection lifecycle, handshake decisions, cancellation, shutdown, limits, and concurrency.
- Typed protocol errors, binary streams, and raw socket support where their use cases justify them.
- OpenRPC contract emission and Python/TypeScript client generation with drift checks.
- FastAPI-first registration, plus Dishka integration consistent with Canon conventions.

Keep the mature RPC core where it remains useful. Remove transport-agnostic *product promises* and unsupported adapter surfaces when they add ongoing complexity; do not delete interface seams needed for isolated testing.

**Non-goal:** Maintain `pyrpckit` and the successor as two actively evolving alternatives.

## 6. Integration model

The intended dependency direction is:

```text
                             APPLICATION
                                  |
                 +----------------+----------------+
                 |                |                |
          fastapi-canon    fastapi-streams   WebSocket RPC
                 |                |                |
                 +---- optional --+--- optional ---+
                       adapters owned by Canon

             FastAPI + Pydantic + Dishka conventions
```

More precisely:

- Canon's **core** must not require either transport extension.
- `fastapi_canon.integrations.streams` may optionally depend on `fastapi-streams`.
- `fastapi_canon.integrations.rpc` may optionally depend on the chosen RPC package.
- Neither transport extension depends on `fastapi-canon`.
- The RPC and Streams packages are not required to depend on each other.
- Do not invent a shared `canon-core` or universal protocol package until concrete duplication and stable shared abstractions justify it.

### 6.1 Integrating Streams

Goal: a stream is a first-class contribution to a Canon feature, respects composition/lifespan/error conventions, and retains its native event schema.

A possible public import is:

```python
from fastapi_canon.integrations.streams import CanonStreamRouter
```

**Illustrative target API only — not an implemented or guaranteed class.** It may prove cleaner to allow a plain `StreamRouter` inside `Feature(routers=[...])`, adding only a small adapter for contract integration. Prefer composition to multiple inheritance or copying both router implementations.

The SSE producer, event encoding, and OpenAPI stream metadata remain owned by `fastapi-streams`. Canon contributes feature wiring and error conventions, not a second streaming engine.

### 6.2 Integrating RPC

Goal: RPC endpoints are feature contributions with deliberate connection and per-call DI scopes, consistent authentication/rejection policies, and explicit lifecycle ownership.

A potential adapter import is:

```python
from fastapi_canon.integrations.rpc import RpcFeatureAdapter
```

**Illustrative target API only.** Prefer reuse of existing FastAPI RPC adapter functionality (`RpcRoutes`, `FastApiSocket`, and Dishka integration from RPCkit) over introducing an entirely new protocol runtime.

Carefully distinguish HTTP error responses, handshake rejections, and established WebSocket error frames: they are not interchangeable.

### 6.3 A consistent developer experience, not forced symmetry

Strive for consistent naming of routers, namespaces, error registries, and operation identifiers. Do **not** force all operations onto one mega-router or one decorator shape if the underlying transports differ.

For example, `CanonRouter`, `StreamRouter`, and an `RpcRouter`-style public API can coexist while registering through a single feature-composition system. The RPC router example is aspirational; its ergonomics and compatibility with existing `RpcChannel`/`RpcService` concepts must be tested before committing to it.

## 7. Documentation and agent experience

The guides are a core product, not marketing collateral. Retain the existing `fastapi-canon` architecture-guide repository's strengths: feature slices, inward dependencies, Dishka, database/migration practices, testing, import conventions, and concise rationale.

Documentation should operate on three levels:

1. **Vision and principles:** This file; what Canon is and is not.
2. **Normative guides:** Short, concrete rules per architectural subject, suitable as agent context.
3. **Reference implementations:** Working examples demonstrating those rules end-to-end.

An agent should be able to read `AGENTS.md`, follow a guided entry point, implement a feature, and execute a prescribed test suite without guessing at architectural boundaries.

Proposed document structure:

```text
VISION.md
README.md
AGENTS.md
guides/
  architecture.md
  application.md
  domain.md
  dependency_injection.md
  presentation.md
  errors.md
  http.md
  streaming.md
  rpc.md
  clients-and-contracts.md
  testing.md
  uv-workspace.md
  releases.md
  migrations.md
docs/
  compatibility.md
  contributing.md
  design-decisions/
examples/
  reference-service/
  agent-runs/
  realtime-browser/
```

Reference applications should cover real interaction patterns rather than trivial demos alone:

- **Agent runs:** REST to create a run; SSE to stream token deltas, tool events, approval/clarification requests, and completion; a separate command route to answer a pending question or stop a run.
- **Remote browser:** REST lifecycle operations, SSE for discrete observable events where appropriate, and WebSocket RPC/raw socket channels for bidirectional control and browser protocol proxying.
- **Feature composition:** Authentication, persistence, errors, providers, and lifespan assembled into a single FastAPI application.

These are reference patterns, not requirements that all agent interaction must use one specific transport.

## 8. Repository architecture

One Git repository, multiple independently published packages, shared documentation, and integration tests:

```text
fastapi-canon/
├── VISION.md
├── README.md
├── AGENTS.md
├── pyproject.toml               # uv workspace coordination
├── uv.lock
├── packages/
│   ├── fastapi-canon/
│   │   ├── pyproject.toml
│   │   ├── fastapi_canon/
│   │   └── tests/
│   ├── fastapi-streams/
│   │   ├── pyproject.toml
│   │   ├── fastapi_streams/
│   │   └── tests/
│   └── websocket-rpc/           # provisional directory name
│       ├── pyproject.toml
│       ├── <final_import_package>/
│       └── tests/
├── guides/
├── docs/
├── examples/
│   ├── reference-service/
│   ├── agent-runs/
│   └── realtime-browser/
├── tests/
│   ├── integration/
│   ├── compatibility/
│   └── packaging/
├── scripts/
└── .github/workflows/
```

Adopt a `uv` workspace for local coordination and one shared lockfile. **The workspace lockfile makes local development reproducible; it does not prove independently published artifacts will resolve or work together.** Separate consumer-style tests are mandatory.

### 8.1 Source consolidation

There are currently two Canon repositories serving distinct purposes:

- `mathisarends/fastapi-canon` — architecture guides and reference service.
- `mathisarends/fastapi_canon` — the Python composition library.

Consolidate both into the new `fastapi-canon` monorepo, retaining documentation quality, package functionality, and attribution/history where practical. Import `fastapi-streams` and the RPCkit implementation as distinct packages, preserving Git history via an intentional migration strategy where feasible.

Avoid importing legacy CI, dependency conventions, and documentation blindly. Reconcile them to a single repository-level quality policy without erasing package-specific tests.

## 9. Compatibility is a release gate

Independent versioning is intentional. Independent compatibility is **not**.

### 9.1 Compatibility policy

- Each package has its own semantic version and changelog.
- Public integration APIs have declared compatibility ranges.
- A supported release combination is recorded in `docs/compatibility.md` (or a machine-readable source that generates it).
- Canon adapters declare tested minimum and maximum-compatible major/minor ranges when justified.
- Canon core continues to work with no transport extensions installed.
- A package release that affects shared interfaces is blocked until dependent adapters and reference applications pass the compatibility matrix.

Example only (not an actual support statement):

```text
Canon A.B  +  Streams C.D  +  WebSocket RPC E.F
    tested as one supported stack combination
```

Avoid a single global stack version as the *only* package version. Optionally publish an ecosystem compatibility snapshot or a constraints file for consumers who want the fully tested combination.

### 9.2 Two required testing modes

**A. Workspace integration**

Test current development versions together from the shared lockfile. This catches integration regressions while making coordinated changes easy.

**B. Distribution integration**

Build wheels/sdists and install them into clean environments **without local `tool.uv.sources` workspace overrides**. Test supported ranges against released versions, especially the minimum supported combination and newest compatible combination. This catches metadata errors, undeclared dependencies, packaging omissions, and version drift.

At minimum, validate:

- The independent installability/importability of every distribution.
- Optional extras resolving only the needed integrations.
- Canon + Streams; Canon + RPC; Canon + both.
- Canon installed without either optional package.
- Python-version and FastAPI/Pydantic/Dishka constraint intersections.
- Artifact contents, entry points, and typed package markers.
- Generated TypeScript/Python clients using the exported contract of the installed server package.

### 9.3 Contract conformance tests

Maintain golden fixtures and consumer-level tests for:

- HTTP routes, `operation_id` stability, typed Problem Details and status mappings.
- SSE event discriminators, incremental/fragmented decoding, end-of-stream semantics, disconnect/cancellation behavior, and schema stability.
- RPC methods, errors, notifications, subscriptions, handshakes, reconnect behavior where implemented, cancellation, and binary/raw socket operations.
- Cross-transport authentication and DI lifecycle rules.
- Generation checks that fail when committed contract artifacts or SDKs are stale.

Security-sensitive cases must include unauthorized handshakes, redaction of internal error details, stream cancellation, resource cleanup, and bounded connection limits.

## 10. Versioning, releases, and automation

A monorepo commit may change multiple packages; a release normally publishes **only the affected distribution(s)**.

Recommended tag convention:

```text
fastapi-canon-v0.5.0
fastapi-streams-v0.2.0
<final-rpc-distribution>-v0.1.0
```

These are **examples**, not existing releases or prescribed next versions. The release pipeline must parse the package identity and version from the tag, compare it to package metadata, build only the matching distribution, run all relevant gates, and publish to that package's configured PyPI Trusted Publisher.

Release flow:

1. A developer or coding agent proposes changes through a PR.
2. CI runs local package tests, cross-package integration tests, contract/golden checks, and distribution installation tests.
3. A changeset or explicit release PR selects impacted packages and versions.
4. A protected release workflow validates the release commit and tag.
5. The workflow builds the specific sdist/wheel, checks metadata, and publishes using **GitHub OIDC / PyPI Trusted Publishing**, without persistent PyPI API tokens in repository secrets.
6. Release notes, versioned documentation, and compatibility records are updated together.

Agents may prepare a release and, within granted permissions, trigger an approved workflow. Do not give arbitrary agent branches unrestricted publishing rights. Use protected branches/environments, least privilege, and a clearly auditable approval boundary.

Breaking changes across integrations require a coordinated release plan; simple isolated fixes should not force artificial version bumps of unrelated packages.

## 11. RPCkit succession and archive plan

**Decision:** `pyrpckit` is to become an **archived predecessor**, not an indefinitely maintained sibling or upstream for a permanent fork.

### Phase 1 — Inventory and preservation

- Inventory public `rpckit` imports, current CLI commands, `RpcService`/`RpcChannel` API, generated client surfaces, and integration behaviors.
- Identify features currently used by applications before removing or redesigning APIs.
- Import source, tests, docs, historical decisions, and license information into the monorepo.
- Preserve runtime semantics and wire compatibility by default; changes must be deliberate and tested.

### Phase 2 — FastAPI-first public API

- Define a focused FastAPI-native router and composition experience, informed by existing `RpcRoutes` and Dishka support.
- Decide whether `RpcService`/`RpcChannel` remain publicly central or become internal building blocks. Avoid renaming solely for aesthetics.
- Keep typed OpenRPC export, generated clients, subscriptions, errors, streams, and raw sockets.
- Simplify unsupported generic transport interfaces where doing so materially improves maintainability.

### Phase 3 — Verified replacement

- Settle a **distinct PyPI distribution name** and Python import path.
- Publish a migration guide: installation, imports, router registration, DI, CLI invocation, codegen output, and behavior changes.
- Validate representative existing consumers and check whether generated client APIs require regeneration or adapters.
- Release a tested successor and update application dependencies.

### Phase 4 — Archive `pyrpckit`

Only after a usable replacement and migration path exist:

- Add a clear archival notice and successor link to the old README.
- Publish a final documentation update or deprecation release if useful.
- Mark the old GitHub repository read-only/archived.
- Keep historical tags, issues, and documentation accessible.
- Stop new feature development on the predecessor.

Archiving should be a deliberate **end state**, not an action performed before consumers have a migration path.

## 12. Code generation strategy

Both Streams and RPC currently provide generated Python/TypeScript clients. This is a unifying value proposition and a potential source of accidental duplication.

Short-term strategy:

- Keep each protocol's code generator inside its owning package.
- Align quality requirements: deterministic output, typed errors, cancellation, zero-drift checks, and readable generated code.
- Make HTTP stream contracts and RPC contracts complementary rather than artificially merging their formats.
- Publish a consistent guide for consumers using REST codegen (such as existing OpenAPI generators), stream codegen, and RPC codegen together.

Long-term possibility:

- Extract common code-generation utilities only when actual reuse is established: naming policy, deterministic file rendering, generator validation, language conventions, or schema helpers.
- Avoid a compulsory unified compiler, intermediate representation, or client runtime without a demonstrated reduction in user complexity.

The experience we want is **define once, generate reliably, verify in CI** — not necessarily **one generator implementation for all transports**.

## 13. What Canon deliberately does not become

- A replacement for FastAPI or Starlette.
- A full-stack framework that controls persistence, jobs, frontend rendering, hosting, or deployment.
- A collection of mandatory wrappers around already idiomatic FastAPI APIs.
- A requirement to install SSE and RPC in an ordinary CRUD application.
- A transport-neutral RPC platform maintained for theoretical use cases.
- A single-package release train where unrelated libraries must share a version.
- An unbounded abstraction layer that hides errors or makes debugging harder.
- A proprietary architecture language that a newcomer must learn before understanding a route.

Canon is a disciplined set of defaults with explicit escape hatches, not an attempt to eliminate FastAPI's extensibility.

## 14. Adoption experience

A successful first encounter should follow this sequence:

1. Read a short README explaining what Canon solves and which package to install.
2. Run a reference service that looks like recognizable FastAPI code.
3. Add a feature using the architecture guide and `Feature`/`Composition` pattern.
4. Add a typed SSE stream without losing FastAPI's dependency and authentication behavior.
5. Add WebSocket RPC only when bidirectional operations are actually needed.
6. Generate typed clients and run contract-drift checks.
7. Upgrade packages with a documented compatibility range rather than guessing.

An experienced developer should find the boundaries predictable. A coding agent should reach the same architecture every time it follows the guides.

## 15. Milestones

### M0 — Consolidate and document

- Establish the monorepo and `uv` workspace.
- Merge both existing Canon repositories' relevant materials.
- Import Streams and RPCkit with tests and history where practical.
- Write this vision, package boundary docs, `AGENTS.md`, and a migration checklist.
- Make existing package tests pass without redesigning all APIs at once.

**Exit criterion:** One repository can reproduce and test the current components.

### M1 — Prove interoperability

- Add a reference service composed with Canon, including a typed stream and RPC endpoint.
- Introduce optional integration modules only where needed.
- Define and automate two-mode testing: workspace + built distributions.
- Publish a compatibility matrix and release policy.

**Exit criterion:** The stack works as installed artifacts, not only through editable workspace imports.

### M2 — FastAPI-first RPC successor

- Finalize the conflict-free distribution name.
- Design and implement the public FastAPI-native RPC API.
- Port necessary RPCkit behavior and contract/codegen tests.
- Document migration and validate application consumers.

**Exit criterion:** The successor can replace RPCkit for intended production use cases.

### M3 — Independent trusted releases and retirement

- Implement per-package tags, release gating, changelogs, and PyPI Trusted Publishing.
- Verify independent package installs, compatibility ranges, and generated clients.
- Publish the successor, migrate consumers, then archive `pyrpckit`.

**Exit criterion:** Every supported component is independently releasable without untested ecosystem drift.

### M4 — Polish the platform experience

- Improve shared docs and agent onboarding.
- Add robust integration examples for agent runs and remote browser control.
- Evaluate optional templates, scaffolding, compatibility snapshots, and codegen convergence based on real pain points.

**Exit criterion:** An agent or developer can start a new service and reliably reproduce Canon's intended architecture.

## 16. How we know this is working

Prefer observable engineering outcomes to popularity metrics alone:

- New features follow stable boundaries with fewer custom architectural decisions.
- No transport extension is required for a Canon-only service.
- Integration breakage is caught before publication, not by downstream applications.
- Generated client drift reliably fails CI.
- An installation from released wheels behaves like the tested workspace.
- Existing RPCkit consumers have a documented, testable migration path.
- Developers can explain which layer owns composition, HTTP contracts, SSE behavior, and WebSocket RPC behavior without ambiguity.
- Coding agents produce recognizable, maintainable FastAPI code with less prompt repetition and fewer architectural corrections.

## 17. Decisions and questions

### Direction agreed

- Use **Canon** as the conceptual umbrella and `fastapi-canon` as the monorepo.
- Preserve independently installable Python distributions.
- Use a shared `uv` development workspace while testing published artifacts separately.
- Use **independent package versions plus a supported compatibility matrix**, not mandatory lockstep versioning.
- Keep `fastapi_canon.integrations.streams` and a corresponding RPC integration as preferred extension points, subject to API design.
- Position the RPC successor as **FastAPI-first**, and **archive `pyrpckit` after migration** instead of maintaining a permanent fork.
- Keep the architecture guides, runnable reference service, and agent experience central to the product.

### Explicitly open

1. What distinct, available PyPI name and import path should the RPC successor use? (`fastapi-wsrpc` collides with `fastapi-ws-rpc` under distribution-name normalization.)
2. Does Streams integration require a `CanonStreamRouter`, or is accepting `StreamRouter` within `Feature` cleaner?
3. Should the RPC public API emphasize `RpcRouter` decorators, retain `RpcChannel`/`RpcService`, or offer both with a carefully limited surface?
4. Which compatibility ranges are committed to support during the initial migration?
5. Should a tested stack snapshot be offered as a constraints file or metapackage later?
6. Which RPC protocol/client APIs must remain wire- and source-compatible for existing applications?
7. Which codegen conventions genuinely benefit from sharing implementation, as opposed to sharing only tests and guidelines?

Resolve these by prototypes and consumer tests, not by creating large abstractions in advance.

---

## Closing statement

**Canon is how we build FastAPI applications.**

It gives developers and coding agents a common architecture, makes public contracts reliable, and adds advanced communication models without sacrificing FastAPI's native simplicity. Each library remains focused. The application, its documentation, its generated clients, and its release compatibility form one coherent system.

The ambition is not *more framework*. It is **less repeated architectural work, less contract drift, and more predictable software**.

### Source projects

- [FastAPI Canon architecture guides](https://github.com/mathisarends/fastapi-canon)
- [fastapi_canon Python library](https://github.com/mathisarends/fastapi_canon)
- [fastapi-streams](https://github.com/mathisarends/fastapi-streams)
- [pyrpckit](https://github.com/mathisarends/pyrpckit)
