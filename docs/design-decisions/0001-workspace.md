# 0001: Consolidate the stack into one uv workspace

Status: accepted for the initial consolidation, 2026-10-17.

## Decision

Use the new `mathisarends/canon` repository as the development workspace. Keep
three distributions under `packages/`, the architecture guides at the root,
and application examples under `examples/`. The repository name can be decided
separately from the existing `fastapi-canon` distribution name.

The user requested consolidation from the source repositories' `origin/main`
branches and incremental commits on `main`. The attached VISION.md supplies
design context and the longer-term target; it does not authorize publication,
repository archival, or implementing every future milestone at once.

## Imported sources

These commits were fetched from each repository's remote `main`, rather than
from local branches or working directories:

| Source repository | Commit | Destination |
| --- | --- | --- |
| `mathisarends/fastapi-canon` | `19447668cb7f554c7271a9f1da15ab7ac4fd0d41` | root guides and reference service; base Git history |
| `mathisarends/fastapi_canon` | `f275d3129671296bc9565155e641488e77d42074` | `packages/fastapi-canon` |
| `mathisarends/fastapi-streams` | `90b70bef93110a1c97c9db38a584093f3bf4ac08` | `packages/fastapi-streams` |
| `mathisarends/pyrpckit` | `853579eb08903bd95f8ce03f7608a3703ba40add` | `packages/websocket-rpc` |

Package imports are explicit merge commits with the source tip as a parent and
the source tree placed under its package prefix. No squash or history rewrite
is needed. `git log --all` and `git show <source-commit>:<original-path>` retain
access to original paths and attribution; path-following does not automatically
cross the prefix move. Later commits reconcile tooling and documentation.

## Boundaries

- Canon owns feature composition, Dishka application lifecycle, and HTTP contracts.
- Streams owns typed SSE contracts and Python/TypeScript stream clients.
- RPC owns its runtime, WebSocket adapter, OpenRPC, and generated clients.
- Canon's optional integrations depend on extensions; extensions do not require
  Canon. There is no new shared core or mandatory stack metapackage.
- Preserve the existing `CanonStreamRouter` integration and its tests from the
  imported Canon tip. The vision's suggested alternative remains a design
  question, not a reason to remove a tested implementation during migration.

## Workspace and testing

The root is a non-published coordination project. It includes all three packages
and the existing reference service in one lockfile. Workspace sources resolve
Canon's Streams extra to the local member. Package metadata retains ordinary
distribution requirements for independent builds.

Run each package suite in its own subprocess and working directory: imported
suites use top-level `tests` and `examples` modules that collide in a single
pytest collection. Keep package-specific lint/type/codegen settings, with a
root command coordinating them. Consolidate CI at `.github/workflows/`.

Build each distribution and install artifacts in fresh environments using
`uv pip`, outside workspace source resolution. Cover core-only installs and
Canon with each extension combination; verify imports, CLIs, typed markers,
and real HTTP/SSE/WebSocket behavior. Do not claim a supported release matrix
solely because a workspace lock resolves.

## Incremental scope

1. Preserve the vision and record this proposal.
2. Import each library in a separate history-preserving commit.
3. Establish the workspace, shared lock, contributor commands, and consolidated CI.
4. Verify package suites, existing client generation, built artifacts, and a
   small composed example before recording compatibility results.

Future work: finalize the RPC successor name and public API through consumer
tests, improve the feature-slice reference service to use Canon composition,
and implement independent protected PyPI releases. Archive the RPC predecessor
only after a released replacement and migration path exist.
