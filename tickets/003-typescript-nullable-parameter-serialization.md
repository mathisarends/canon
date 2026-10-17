# 003 — Define consistent null handling for optional HTTP parameters

Status: Open
Priority: P2
Scope: TypeScript transport template, generated parameter types, HTTP tests

## Problem

Generated TypeScript signatures permit `null` for nullable FastAPI parameters.
`appendQuery()` skips `undefined`, but converts `null` to the string `"null"`.
This is not the server's null/omission representation. A valid typed call can
produce HTTP 422, or send the literal string `"null"` where omission was intended.

The Python runtime already omits scalar `None` query/header values. The two SDKs
therefore have different wire behavior for the same optional nullable parameter.
`setHeader()` has the same TypeScript conversion pattern and needs coverage too.

## Relevant code

- `fastapi_streams/codegen/templates/sse.ts`: `appendQuery()` and `setHeader()`
  (review baseline: lines 32–57).
- `fastapi_streams/codegen/templates/python/runtime.py`: corresponding Python
  helpers, useful as a comparison for omission behavior.
- `tests/typescript/sse.test.ts` and real HTTP integration fixtures/tests.

## Reproduction

Define a finite stream with `limit: int | None = None`. Export and generate its
TypeScript client. The generated argument permits `limit: null`.

```typescript
const query = new URLSearchParams();
appendQuery(query, "limit", null, true);
console.log(query.toString()); // limit=null
```

Against the FastAPI route:

- `GET /events` returns 200.
- `GET /events?limit=null` returns 422.

Both server outcomes were reproduced with `TestClient`, and the query encoding
was reproduced by executing the generated TypeScript transport under Node.

## Proposed implementation

Define and document omission semantics for optional scalar query and header
parameters. For these parameters, treating `null` like omission would align with
the Python SDK and common FastAPI defaults.

Account explicitly for required nullable parameters: do not claim that omitting
a required parameter implements a JSON null value. Either provide supported wire
semantics, reject an unrepresentable value clearly, or narrow the generated API.
This decision should be visible in tests and documentation.

Preserve the actual string `"null"`. Do not silently remove array elements or
change empty-string, boolean, zero, or query-array explode behavior as a side
effect of the fix.

## Acceptance criteria

- Passing `null` to an optional nullable integer query parameter no longer
  silently produces `?limit=null` and a 422 response.
- Optional nullable header parameters have a consistent, tested policy.
- Python and TypeScript agree on omission for supported optional scalar cases.
- Required nullable parameters have an explicit tested policy.
- A string value equal to `"null"`, `false`, `0`, and `""` retain their intended
  serialization; existing array explode tests still pass.
- Include a generated-client-to-FastAPI regression in addition to helper tests.
- Update templates, regenerate artifacts, and document the chosen behavior.

## Validation

Run `npm test`, `npm run typecheck`, relevant real HTTP integration tests, the
complete Python suite if shared IR/types change, and generated-artifact checks.
