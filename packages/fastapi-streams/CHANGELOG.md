# Changelog

All notable changes and consumer upgrade steps are recorded here. Entries marked
unreleased describe prepared source versions that have not been published.

## 0.2.0 - unreleased

- Fix PyPI installation instructions and supported-scope wording. Replace the predecessor release guide with the workspace release process.

## 0.1.0 - 2026-10-17

### Added

- Generated TypeScript JSDoc and Python method docstrings include OpenAPI
  summaries, descriptions, deprecation, and SDK-specific iteration, cancellation,
  validation, and error behavior. Endpoint descriptions remain the source for
  business guarantees such as retention or job lifetime after disconnect.
- `OptionalDiscriminatorWarning` identifies optional discriminator fields in
  stream event unions, including nested and referenced events. Diagnostics name
  the operation, route, model, and field; generation preserves schema requiredness.
- Explicit `OperationErrorBody` aliases in both SDKs distinguish declared HTTP
  response bodies from thrown exceptions. Existing `OperationError` aliases remain
  available; TypeScript marks them deprecated. Method documentation lists the
  declared HTTP statuses and media types. Existing Python anonymous error-model
  imports such as `OperationError0` retain their names.
- TypeScript `isHttpError(error, isDetails)` narrows `HttpError.details` only after
  a caller-supplied type guard succeeds. It adds no runtime dependencies or assumed
  problem format. HTTP status and operation provenance remain caller checks.
- Checked TypeScript and Python error-handling consumer examples, plus a
  standalone FastAPI dependency/problem-response regression without an error
  framework. Public generated error-alias name collisions now fail explicitly.

### Changed

- Develop in `mathisarends/canon`; package source, documentation, and issue URLs
  now point to the monorepo.
- Single-value string fields now use TypeScript/Python literals instead of
  synthesizing a separate public constant object or `StrEnum` for every field.
  Explicitly named enums, multi-value field enums, and shared event discriminator
  enums remain available. TypeScript also omits unnecessary property quotes and
  union parentheses while preserving intersection grouping and extra-field types.

### Breaking generated-code changes

- Synthesized single-field constants such as `InvalidCredentialsProblemTitle`
  and `InvalidCredentialsProblemType` are no longer exported. Replace usages like
  `InvalidCredentialsProblemTitle.INVALID_CREDENTIALS` with the wire literal
  `"Invalid credentials"`, then remove unused imports. Python singleton fields
  now contain plain strings instead of generated `StrEnum` members; replace
  identity checks with value comparisons. Shared discriminator values such as
  `RunEventType.RUN_STARTED` and explicit schema enums are unchanged.
- Generated `OperationError`/`OperationErrorBody` names are reserved in both
  SDKs. Python now reports collisions explicitly too. If a schema uses one of
  these names, rename the colliding model or choose a distinct `operation_id`.

### Upgrade from 0.0.1

1. Update `fastapi-streams[codegen]` to `0.1.0`, using the same version for schema
   export and both SDKs.
2. Regenerate committed clients from the application's OpenAPI document. Existing
   method names and call signatures are unchanged:

   ```sh
   uv run fastapi-streams schema --app your_app:app --output openapi.json
   uv run fastapi-streams generate --schema openapi.json --language typescript --output generated/typescript
   uv run fastapi-streams generate --schema openapi.json --language python --output generated/python
   uv run fastapi-streams check --app your_app:app --schema openapi.json --language typescript --output generated/typescript
   uv run fastapi-streams check --app your_app:app --schema openapi.json --language python --output generated/python
   ```

   Substitute the application's existing module and output paths. Preserve
   `--python-http-client httpx2` on generation and checks if it is already used.
3. Review optional discriminator warnings. For output-only Pydantic event models
   whose defaults are always serialized, see the serialization configuration in
   [the codegen guide](docs/codegen.md#event-discriminators). Do not make optional
   request fields required merely because they have Python defaults. Add
   endpoint-specific guarantees to OpenAPI descriptions. Export and regenerate
   again after changing models or descriptions.
4. Apply the single-field constant migration above if the application imported
   these generated names. HTTP payloads, method names, and signatures are unchanged.
5. Prefer `OperationErrorBody` over `OperationError` when referring to response
   bodies. Keep caught errors unknown until checked; validate `HttpError.details`
   with a body guard in TypeScript or Pydantic `TypeAdapter` in Python. See
   [HTTP error contracts](docs/clients.md#http-error-contracts). Unexpected proxy
   responses must continue through the generic `HttpError` fallback.
6. Run the consuming project's TypeScript/Python type checks and stream tests.
   Commit the exported schema and regenerated SDKs together with call-site updates.

## 0.0.1

- Initial typed GET/POST JSON SSE routers, OpenAPI export, TypeScript and Python
  generators, shared transports, and contract/client drift checks.
