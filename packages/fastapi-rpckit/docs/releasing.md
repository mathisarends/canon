# Releasing fastapi-rpckit

The successor is currently 0.1.0, unreleased. Follow the workspace
[release policy](../../../docs/releases.md). Canon and Streams remain separate
PyPI distributions with independent versions; the RPC successor is a third.

Before publication, confirm the PyPI name is accepted, configure a protected
Trusted Publisher for this repository, and implement package-prefixed release
tags. The imported nested workflows use the predecessor's repository layout and
are historical references, not the release path for the new package.

Update `pyproject.toml`, `fastapi_rpckit.__version__`, and `CHANGELOG.md` together,
then update the root lockfile. Run the workspace gates, built-distribution tests,
and generator drift checks described in the root contributor guide. Validate
existing application consumers using the migration guide before declaring the
successor production-ready. No release is triggered by the workspace migration.
