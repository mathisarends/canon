# 0002: Apply integration feedback without replacing working transports

Status: accepted for source preparation, 2026-10-18.

The consumer report reviewed published Canon 0.5.0, Streams 0.1.0 and RPCkit 0.1.0
in Maximus Trading. Its integration results are reported by the consumer agent;
local tests verify the changes below, not a full external application migration.
The user authorized incremental commits on main and release preparation, including
breaking changes. Publication remains a separate explicit action.

## Decisions

1. Fix incorrect active installation guidance and the removed FastAPI-extra
   diagnostic. Check active examples against metadata without rewriting history.
2. Use package-root FastAPI imports as the RPC public API. Keep `RpcRoutes` for
   clarity and preserve the existing nested imports. Moving implementation files
   or renaming working public types adds no needed behavior.
3. Type `dishka_router` options explicitly and allow a custom resolver factory.
   Its context is a value. Per-connection FastAPI dependencies and rejection
   bindings use `RpcRoutes`; a tested example covers cookie/Origin checks,
   credential expiry, and Dishka APP/SESSION/REQUEST responsibilities. Do not add
   a second context-factory abstraction to hide those semantics.
4. Keep native SSE transport ownership in the application. Describe reviewed
   payloads with an explicit OpenAPI contract and generate directly from it.
5. Keep one authoritative OpenAPI 3.2 artifact. Provide a tested private 3.1
   codegen-view example retaining event-model references. It is deliberately
   scoped to ordinary REST plus inline JSON SSE, not a universal downgrade API.
6. Preserve string pattern/length and numeric bounds/multiples through the IR
   into Python models. Diagnose unsupported rules and document Pydantic's limits.
   Regeneration tightens validation, so Streams advances to 0.2.0. TypeScript
   continues to provide static types without runtime schema validation.
7. Keep Python unknown variants strict by default. A request can ignore unknown
   string tags only for a top-level discriminated union. Invalid JSON, missing
   tags, malformed known variants and unknown nested variants still fail. This
   policy does not add reconnect, retry or replay behavior.

Canon advances to 0.5.1 for the updated optional Streams pin and guidance; RPCkit
advances to 0.2.0 because the explicit mounting signature and stricter context
acceptance are classified as breaking source API changes. The initially prepared
0.1.1 was never published and is superseded. Before 1.0, any breaking change
requires the next minor version with patch zero. Versions remain independent.
Exported wire names are unchanged. Full Maximus/Cara tests,
old-repository changes and real publication remain separate work.
