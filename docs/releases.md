# Independent releases

`fastapi-canon` and `fastapi-streams` retain their existing PyPI identities
and import paths. `fastapi-wsrpc` is the unreleased RPC successor.
A monorepo change does not require releasing all components.

## Prepared versions, 2026-10-17

| Distribution | Last published | Prepared source version | Reason |
| --- | --- | --- | --- |
| `fastapi-canon` | 0.4.0 | 0.5.0 | Public `CanonStreamRouter` and `HTTPMethod`; integration pins Streams 0.1.0. |
| `fastapi-streams` | 0.0.1 | 0.1.0 | Generated literal/enum changes, reserved error aliases, diagnostics and SDK documentation. |
| `fastapi-wsrpc` | None | 0.1.0 | First successor release; pyrpckit 0.11.0 runtime and wire behavior retained. |

These are prepared, unpublished versions. Changelog sections deliberately remain
marked unreleased; set their actual publication dates when releasing. Canon and
Streams were compared with the published PyPI wheels, including verifying their
download hashes. Canon adds its optional integration and public exports; Streams
changes its codegen modules/templates and adds diagnostics/documentation helpers.
Its runtime transport and endpoint calling conventions remain unchanged, but
consumers must apply the generated-code migrations in its changelog.

The root pins, Canon's optional/development Streams pins, version constants and
root lockfile agree. The reference service now requires Canon `>=0.5,<0.6`.
Package URLs point to this repository and the relevant package/docs directories.
Streams must be published before Canon's `streams` extra can resolve from PyPI.
RPC can be published independently; no shared version number is required.

Use future package tags `fastapi-canon-v0.5.0`, `fastapi-streams-v0.1.0`, and
`fastapi-wsrpc-v0.1.0`. No tags or releases have been created by this preparation.

## Local preparation gates

```console
uv sync --locked --all-packages --all-groups
npm ci --ignore-scripts --prefix packages/fastapi-streams
uv run --locked python scripts/check.py all
uv run --locked python scripts/check_distributions.py
uv run --locked python scripts/check_distributions.py --python 3.12 --dependencies minimum
uv run --locked python scripts/check_streams_artifacts.py
```

The distribution checks build wheels from sdists, verify metadata and typed
markers, and install in fresh environments without workspace overrides. The
minimum mode exposes runtime and requested-extra dependencies as direct resolver
requirements and uses `lowest-direct`, selecting the lowest jointly satisfiable
versions. Other transitive dependencies resolve normally. It covers six library
combinations; the default latest mode also checks the installed reference service.
Each mode writes a machine-readable inventory to `dist/compatibility-MODE.json`.
See [compatibility results](compatibility.md) for the tested scope and
[RPC parity/consumer checks](rpc-parity.md) for repeatable SDK verification.

Regenerate example clients through their generators before checking drift:

```console
uv run --locked --directory packages/fastapi-streams python scripts/codegen.py
uv run --locked --directory packages/fastapi-wsrpc python -m fastapi_wsrpc.codegen.cli generate --config examples/generated_clients/rpcgen.toml
uv run --locked python scripts/check.py clients
```

## Deferred publisher and CI setup

The user deferred CI/release-workflow setup on 2026-10-17. The root publishing
workflow, protected environment and dry run remain future work; local preparation
does not implement or activate them.

The public `fastapi-wsrpc` PyPI JSON endpoint still returned 404 on this date.
The account publisher page redirected to login, so neither name acceptance nor
the account's Pending Publisher was verified. A 404 does not establish name
acceptance. After sign-in, use [account publishing](https://pypi.org/manage/account/publishing/)
to check/configure the intended pending publisher:

| Field | Intended value, to match the eventual workflow |
| --- | --- |
| PyPI project | `fastapi-wsrpc` |
| GitHub owner | `mathisarends` |
| Repository | `canon` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

Per [PyPI's pending-publisher instructions](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
this registration does not reserve the name. The first successful publication
creates the project. Check the two existing projects' monorepo publishers
separately. No account configuration or publication was performed here.

## Future publication gate

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
