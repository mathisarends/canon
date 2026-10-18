# 0004: Keep SDK validation at boundaries and remove repeated setup work

Status: implemented; local release preparation, 2026-10-18.

The latest Maximus report exercises Canon 0.5.2, Streams 0.3.0 and RPCkit 0.2.0.
It reports successful request validation, structured errors and strict drift
checks, with 19 exactly reviewed UUID/date-time/URI-reference limitations. These
are consumer-reported integration results. They neither identify a new migration
blocker nor establish exhaustive application or deployment coverage.

The user authorized sequential implementation and isolated commits on main, plus
a next-release proposal. The user subsequently authorized both package
publications with matching GitHub Releases on 2026-10-18; see the release guide.

## Decisions

1. Keep schema checks at transport boundaries. Generated Python requests validate
   locally for early feedback; server request validation remains authoritative.
   Domain rules, authorization and resource state checks have their own purposes.
   Reuse parsed event models inside a process rather than repeatedly converting
   them to dictionaries and validating the same schema. Canon adds no second
   event-validation layer.
2. Preserve generated Python adapters and direct `validate_json` on valid events.
   Reuse the JSON-value adapter on HTTP errors and skipped unknown events. Cache
   discriminator metadata lazily per generated event adapter, retaining existing
   method signatures instead of introducing new policy arguments. Skipped events
   do not need sanitized public exception details. Invalid JSON, malformed known
   events, missing/non-string tags and unknown nested variants still fail.
3. Add provenance and boundary capabilities to the existing optional diagnostic
   report, retaining version 1 and every existing diagnostic identity/allowance.
   The report identifies complete schema content, generator version, target and
   selected HTTP backend. It distinguishes request-call, event-iteration and
   consumer-controlled HTTP-error validation. It explicitly disclaims full JSON
   Schema equivalence and adds no SDK runtime work.
4. Keep TypeScript static-only by default. A supported optional runtime decoder
   remains deferred until an application needs it. This change adds neither a
   validator dependency nor a broad validation-disable switch.
5. Prepare Streams 0.3.1 and Canon 0.5.3 as unpublished patch releases. Public
   signatures, accepted inputs, coercion, validation timing and wire contracts
   are unchanged. Canon only updates its optional/development Streams pin;
   RPCkit remains 0.2.0. Publish Streams before Canon if separately authorized.

## Performance evidence

The benchmark harness in `packages/fastapi-streams/scripts/benchmark_runtime.py`
generates Python and TypeScript SDKs for one contract. It separates request
preparation, decoding, framing and complete in-memory stream consumption. Cases
include Unicode token events, nested batches, seven-byte fragments and Python
unknown-event ignoring. It does not make different SDK guarantees equivalent.

Initial Windows/Python 3.14/Node 24 runs identified repeated JSON-adapter
construction as a substantial cost in the ignore path. A sequential comparison
uses the same root interpreter, dependencies and harness, with the original
Streams package source from `eb2b9fb` and the optimized runtime committed in
`9c7d8b4`. Each stream contains 100 input events (101 in the ignore case), with
30 iterations, seven rounds and a separate traced peak-memory sample.

| Complete Python stream case | Before, median microseconds/input event | After, median microseconds/input event |
| --- | ---: | ---: |
| Small valid events | 13.823 | 13.864 |
| Nested valid events | 167.326 | 169.776 |
| Unknown events ignored, then one known event | 989.674 | 9.672 |

Reports are local generated evidence at `dist/streams-python-before.json` and
`dist/streams-python-after.json`; the original two-runtime baseline is
`dist/streams-baseline.json`. Wall times vary substantially on this shared host;
the table does not establish deployment latency or a universal speedup. It shows
the targeted ignore-path improvement while the sampled ordinary paths remain
similar. Framing is a substantial part of the nested-event case, so further
schema checks would not address its dominant measured cost. No timing threshold
is added to CI. See the Streams development guide for reproducible commands and
measurement limits.

In the separate traced-memory sample, the ignore case's peak falls from 89,183
to 33,660 bytes per batch; small/nested valid-event peaks are similar. These
figures measure temporary traced peak memory, not allocation counts or total
process memory.

## Release acceptance

Run workspace lint/types/tests and generated-client drift/TypeScript coverage,
the independent current/minimum wheel matrices and installed Streams CLI checks
with each backend separately. Preserve structured failures, caller cancellation,
response cleanup, HTTP errors and application error events. Exact-source CI,
release dry runs, final changelog dates and explicit publication authorization
remain separate release gates. Native Hermes and full external application
validation remain consumer responsibilities, rather than claims of this harness.
