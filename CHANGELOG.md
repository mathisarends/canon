# Changelog

All notable changes and consumer upgrade steps are recorded here. Unreleased
entries describe the next release; they do not change the installed version.

## Unreleased

### Added

- Generated TypeScript JSDoc and Python method docstrings include OpenAPI
  summaries, descriptions, deprecation, and SDK-specific iteration, cancellation,
  validation, and error behavior. Endpoint descriptions remain the source for
  business guarantees such as retention or job lifetime after disconnect.
- `OptionalDiscriminatorWarning` identifies optional discriminator fields in
  stream event unions, including nested and referenced events. Diagnostics name
  the operation, route, model, and field; generation preserves schema requiredness.

### Changed

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

### Upgrade from 0.0.1

1. Update the `fastapi-streams[codegen]` dependency to the release containing
   these entries, using the same version for schema export and both SDKs.
2. Regenerate committed clients from the application's OpenAPI document. No
   method names or call signatures change in the documentation update:

   ```sh
   uv run fastapi-streams schema --app your_app:app --output openapi.json
   uv run fastapi-streams generate --schema openapi.json --language typescript --output generated/typescript
   uv run fastapi-streams generate --schema openapi.json --language python --output generated/python
   uv run fastapi-streams check --app your_app:app --schema openapi.json --language typescript --output generated/typescript
   uv run fastapi-streams check --app your_app:app --schema openapi.json --language python --output generated/python
   ```

   Substitute the application's existing module and output paths. Preserve
   `--python-http-client httpx2` on generation and checks if it is already used.
3. Run the consuming project's TypeScript/Python type checks and stream tests.
   Add endpoint-specific guarantees to OpenAPI descriptions, rather than editing
   generated documentation.
4. Review optional discriminator warnings. For output-only Pydantic event models
   whose defaults are always serialized, see the serialization configuration in
   [the codegen guide](docs/codegen.md#event-discriminators). Do not make optional
   request fields required merely because they have Python defaults.
5. Apply the single-field constant migration above if the application imported
   these generated names. HTTP payloads, method names, and signatures are unchanged.

## 0.0.1

- Initial typed GET/POST JSON SSE routers, OpenAPI export, TypeScript and Python
  generators, shared transports, and contract/client drift checks.
