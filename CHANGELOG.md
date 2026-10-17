# Changelog

All notable changes and consumer upgrade steps are recorded here. Unreleased
entries describe the next release; they do not change the installed version.

## Unreleased

### Added

- Generated TypeScript JSDoc and Python method docstrings include OpenAPI
  summaries, descriptions, deprecation, and SDK-specific iteration, cancellation,
  validation, and error behavior. Endpoint descriptions remain the source for
  business guarantees such as retention or job lifetime after disconnect.

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

## 0.0.1

- Initial typed GET/POST JSON SSE routers, OpenAPI export, TypeScript and Python
  generators, shared transports, and contract/client drift checks.
