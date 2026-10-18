# 0003: Harden generated Python requests and source diagnostics

Status: accepted for implementation and release preparation, 2026-10-18.

The consumer reports 1,245 Python and 476 native Hermes tests passing on Canon
0.5.1, RPCkit 0.2.0 and Streams 0.2.0. These are consumer-reported results, not a
locally verified full application migration. The new findings concern generated
Streams SDK validation and diagnostics. The user authorized implementation on
main and release preparation, with separate approval before publication.

## Decisions

1. Validate supported Python path/query/header constraints at the ordinary method
   call, matching existing JSON body validation. HTTP starts on iteration.
   Cache adapters and preserve valid wire encoding, numeric representations,
   optional omission, query array explosion and body aliases. Retain Pydantic's
   existing coercion policy rather than adding global strict typing.
2. Collect source diagnostics from schemas reachable through streaming operation
   parameters, bodies, event data and declared HTTP errors. Include original
   pointers, keyword/value, target and operation provenance. TypeScript diagnoses
   scalar constraints that only Python enforces; neither target promises complete
   JSON Schema validation.
3. Provide deterministic JSON diagnostics and optional strict CI enforcement with
   exact reviewed IDs and reasons. Identities exclude prose but include the source
   location, constraint/value, target and operation. Reject stale/duplicate
   allowances; policy failures must not modify generated clients. Enforce this
   policy in the repository's existing drift gate.
4. Add operation ID, JSON/schema category and structured Pydantic details to
   Python StreamParseError. Exclude input/context from public details; retain the
   existing constructor, raw data and exception chain. No automatic logging.
   Preserve unknown-event behavior and known-event validation on both backends.
5. Prepare Streams 0.3.0 because accepted request inputs become stricter. Canon
   0.5.2 updates its optional pin; RPCkit is unchanged. Regeneration and consumer
   call-site tests are required. Existing published-version records remain intact
   until publication and artifact verification complete.

## Validation

Cover negative requests without transport invocation, valid serialization,
structured stream failures, original inline/reference pointers and CI allowances.
Use both HTTP backends, strict generated type checks and actual installed wheels,
plus the workspace's current/minimum dependency matrices. Full external project
validation remains a consumer-side step after adopting regenerated SDKs.
