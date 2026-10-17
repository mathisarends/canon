# Releasing fastapi-rpckit

The first successor release is 0.1.0, published on 2026-10-17. Follow the workspace
[release policy](../../../docs/releases.md). Canon and Streams remain separate
PyPI distributions with independent versions; the RPC successor is a third.

PyPI Trusted Publishing is configured for `mathisarends/canon`, workflow
`release.yml`, environment `pypi`. Tags use `fastapi-rpckit-vX.Y.Z`, and the
[central release list](https://github.com/mathisarends/canon/releases) contains
each workspace library's independent releases. The imported nested workflows
are historical references; only the root workflow executes.

Update `pyproject.toml`, `fastapi_rpckit.__version__`, and `CHANGELOG.md` together,
then update the root lockfile. Run the workspace gates, built-distribution tests,
and generator drift checks described in the root contributor guide. Validate
existing application consumers using the migration guide before declaring the
successor production-ready. Real publication requires explicit user authorization;
dispatch the root workflow with the prepared new version after its CI passes.
