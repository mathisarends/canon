# Releasing rpckit

The current release version is 0.11.0. During development, keep the changelog
heading `Unreleased`. Assign a release date and tag only after validation passes.

## Compatibility during 0.x

Minor releases may change public APIs and generated client layouts. Record each
breaking change in `CHANGELOG.md` and add concrete migration steps. Consumers
regenerate their Python and TypeScript clients from the new contract when they
upgrade. Renamed names do not get compatibility aliases, and generated clients
do not add a separate version handshake. Keep only the intended API: remove
superseded options, callbacks, wrappers, and parallel legacy implementations
rather than introducing deprecation adapters. Document migrations for custom
transports as well as generated client call sites.

## Release checklist

1. Confirm `pyproject.toml`, `rpckit.__version__`, and the changelog heading
   name the same version. Run `uv lock` after changing package metadata.
2. Regenerate the committed examples with
   `uv run rpckit generate --config examples/generated_clients/rpcgen.toml`.
   Then run the same command with `--check`.
3. Run `uv run ruff check .`, `uv run ruff format --check .`,
   `uv run python scripts/verify_types.py`, and `uv run pytest`.
4. Add migration steps for the release and replace `Unreleased` in the
   changelog heading with the release date (`YYYY-MM-DD`). Build with `uv build`
   and inspect the wheel and source archive.
5. Commit the release, tag that commit `v<version>`, and publish the matching
   artifacts. Push the commit and tag together. Start the next version with a
   new `Unreleased` heading.

The release gate uses this repository's tests and generated-client checks.

Publish only the artifacts for the intended version; `dist/` may contain older
builds. For 0.11.0, use:

```bash
uv publish dist/pyrpckit-0.11.0-py3-none-any.whl dist/pyrpckit-0.11.0.tar.gz
```

Authenticate with a PyPI API token, using `__token__` as the username and the
token as the password, or supply the token through `UV_PUBLISH_TOKEN`.
