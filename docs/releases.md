# Independent releases

`fastapi-canon` and `fastapi-streams` retain their existing PyPI identities,
versions, and import paths. `fastapi-wsrpc` is the unreleased RPC successor.
A monorepo change does not require releasing all components.

Each library keeps its own `CHANGELOG.md` and `pyproject.toml`. A future root
release workflow must select exactly one package from a package-prefixed tag,
validate its metadata and changelog, run the relevant package, compatibility,
installed-artifact, and client-drift gates, and build only that package.

Use GitHub OIDC / PyPI Trusted Publishing with protected environments and
repository-specific publisher configuration. No publishing workflow is activated
by this migration. The imported package workflows were written for their old
repositories and tag schemes and remain inert beneath `packages/`.

Before the first release from here:

- Confirm ownership and availability of the final RPC distribution name.
- Document the supported dependency and package-version combinations, including
  independent minimum-version and newest-compatible dependency tests.
- Configure a Trusted Publisher for each package and this repository.
- Validate package-specific tag parsing, branch ancestry, and artifact contents.
- Test the RPC consumer/import/CLI migration and generated clients.

Existing source repositories stay available. A future RPC predecessor archival
requires a usable published successor and an explicit migration decision.
