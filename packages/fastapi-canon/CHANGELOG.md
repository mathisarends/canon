# Changelog

All notable changes to `fastapi-canon` are documented in this file.

## 0.5.1 - 2026-10-18

- Source preparation passed workspace CI, independent wheel matrices and the
  package release dry run. See the [release preparation evidence](../../docs/releases.md#verified-follow-up-preparation-2026-10-18).

- Pin the optional Streams integration and development tooling to 0.2.0.
  Regenerated Python SDKs now enforce supported scalar constraints; follow the
  [Streams upgrade notes](../fastapi-streams/CHANGELOG.md). Canon core remains
  independent of Streams and RPCkit.

- Correct Streams integration installation examples to match the pinned dependency.

## 0.5.0 - 2026-10-17

### Added

- Public `HTTPMethod` string enum, re-exported from Python's `http` module for
  explicit method lists on REST and stream endpoints.
- Optional `CanonStreamRouter` in `fastapi_canon.integrations.streams`, combining
  native fastapi-streams GET/POST SSE generators with canon's error registry,
  router-wide and local `raises=`, and RFC 9457 HTTP problems from dependencies.
  `Feature` automatically discovers its registry; full native SSE event schemas
  are retained for Python and TypeScript client generation.
- A `streams` extra pinned to `fastapi-streams==0.1.0`, with
  independent core imports and a separate codegen development group.
- An integration API guide in `docs/streams.md` and an executable streaming
  example with Dishka-injected request services, documenting installation,
  HTTP method selection, client generation, and the boundary between
  pre-response HTTP problems, in-stream business error
  events, and transport failures.
- Workspace integration checks, both client generators, and clean-wheel core
  runtime checks without Streams. Imported upstream workflow files are historical;
  the root workflow owns CI in the monorepo.

### Changed

- Develop in `mathisarends/canon` and point package metadata to its package and
  documentation directories. Publish Streams 0.1.0 before Canon 0.5.0 because
  the optional integration pins that version.
- Consumers moving from Streams 0.0.1 must regenerate SDKs and follow its
  single-value enum and reserved error-alias migrations.

## 0.4.0 - 2026-09-10

### Added

- Added `validate_openapi_contracts(app)` and `Composition.validate(app)` as
  intention-revealing OpenAPI contract validation entry points.
- Added `install_openapi_contracts(app)` for low-level success-only
  applications. `Composition` installs the compiler automatically even when no
  error registry exists.

### Changed

- Renamed the `CanonRouter` registry parameter from `errors=` to
  `error_registry=` to distinguish the available error catalog from the
  router-level and operation-level errors declared through `raises=`.
- `Feature` now collects error registries from its direct `CanonRouter`
  contributions when `errors=` is omitted. Identical registry contributions
  across features are merged once.

### Fixed

- Made `CanonRouter` success responses self-contained so standalone JSON and
  bodyless routes no longer expose internal `x-fastapi-canon-success` metadata
  or retain FastAPI's generated JSON content.

## 0.3.0 - 2026-09-10

### Added

- Added `CanonRouter` as the canonical route declaration API, with composable
  router-level and operation-level `raises=` declarations plus a first-class
  `response=` success contract. The lower-level response compilers remain
  supported for ordinary FastAPI routers and migrations.
- Added `CanonResponse.responses()` so success-only routes can declare and
  compile response contracts without an empty `ErrorRegistry`.
- Added `ResponseConfigurationError` for FastAPI `response_model` declarations
  that conflict with a bodyless `CanonResponse`.

### Changed

- Compile response contracts from generated OpenAPI operations through the
  documented `app.openapi` hook, removing internal route-tree traversal and
  route-list copying during installation preflight.
- Validate application-level operation contracts at OpenAPI generation time.
  Plain `APIRouter` declarations no longer inspect runtime status or response
  models; use `CanonRouter` for explicit declaration checks. Hidden routes are
  outside document-level validation.

- Renamed the public success contract from `Response` to `CanonResponse` to
  avoid collisions with response classes commonly used in FastAPI routers.

### Fixed

- Bodyless non-204 success contracts now suppress FastAPI's generated JSON
  response without requiring a matching `response_class` on the route.

## 0.2.0 - 2026-09-10

### Added

- Required feature names and feature-aware composition diagnostics.
- Composition-level `router_factory` support for shared prefixes, tags,
  dependencies, and custom `APIRouter` subclasses.
- Lazy Dishka provider construction from provider classes and zero-argument
  factories.
- Reusable normalized HTTP exception contracts through
  `ErrorRegistry.responses(http_statuses=[...])`.
- Immutable success response contracts through `Response` and the `json()`,
  `empty()`, `stream()`, `binary()`, and `sse()` constructors.
- Combined success, domain-error, and normalized HTTP documentation through the
  `success=` argument to `ErrorRegistry.responses()`.

### Changed

- OpenAPI compilation replaces FastAPI's generated success media type when a
  `Response` contract is declared.
- Documentation now defines composition ownership of the generated Dishka
  container and safe handling of public Problem Details fields.

### Fixed

- Manual FastAPI response definitions without canon metadata are accepted.
- SSE, PDF, readiness, and other non-problem response contracts remain valid
  when an error registry is installed.
- Domain codes that conflict with generated `http_<status>` discriminator values
  are rejected during response compilation.

## 0.1.0 - 2026-09-10

### Added

- Immutable feature composition for FastAPI routers, Dishka providers, error
  registries, exception handlers, and lifespans.
- RFC 9457 Problem Details rendering shared by runtime handlers and OpenAPI.
- Domain, validation, HTTP exception, response-validation, and unhandled-error
  normalization.
