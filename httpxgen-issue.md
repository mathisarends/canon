# Support OpenAPI 3.2 and discover SSE payload models through itemSchema/contentSchema

This is an issue draft, not a submitted upstream issue.

## Context and evidence

A consumer migration in Maximus Trading on 18 October 2026 reported this with
`httpxgen==0.3.0`, `fastapi-streams==0.1.0` and `fastapi-canon==0.5.0`:

- The authoritative contract is OpenAPI 3.2 and contains ordinary REST operations
  and SSE operations using Media Type Object `itemSchema`.
- httpxgen rejects the document version before the consumer's REST operation
  filtering runs. The consumer reports support for OpenAPI 3.0/3.1 in that version.
- Its model-retention traversal does not follow `itemSchema` to
  `properties.data.contentSchema`, so event models needed by its high-level HTTP
  client are lost unless a compatibility copy adds a conventional schema reference.
  The consumer uses `schema_tags=["sse"]` for model selection.

These httpxgen observations come from the consumer report; this repository has not
independently reproduced httpxgen's behavior or established its current support
beyond that pinned version. The Canon tests verify our standard SSE contract,
standalone client generation and private compatibility-view example.

## Minimal contract shape

The following reduced example includes a REST operation and a JSON SSE payload:

```json
{
  "openapi": "3.2.0",
  "info": {"title": "Mixed API", "version": "1.0.0"},
  "paths": {
    "/health": {
      "get": {
        "operationId": "health",
        "responses": {
          "200": {
            "description": "Healthy",
            "content": {"application/json": {"schema": {"type": "string"}}}
          }
        }
      }
    },
    "/events": {
      "get": {
        "operationId": "events",
        "tags": ["sse"],
        "responses": {
          "200": {
            "description": "Events",
            "content": {
              "text/event-stream": {
                "itemSchema": {
                  "type": "object",
                  "required": ["data"],
                  "properties": {
                    "data": {
                      "type": "string",
                      "contentMediaType": "application/json",
                      "contentSchema": {"$ref": "#/components/schemas/Event"}
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Event": {
        "type": "object",
        "required": ["type", "run_id"],
        "properties": {
          "type": {"const": "started", "type": "string"},
          "run_id": {"type": "string", "pattern": "^run_[A-Za-z0-9_-]+$"}
        }
      }
    }
  }
}
```

For a full generated contract, export the executable Canon example:

```console
uv run --locked --directory packages/fastapi-streams fastapi-streams schema --app examples.native_proxy:app --output ../../dist/native.openapi.json
```

Apply the consuming application's existing httpxgen invocation and REST filters to
the saved contract. Attach that exact invocation and traceback when submitting;
this draft intentionally does not invent an unverified httpxgen CLI or API.
For a minimal model-selection regression, retain Event through ordinary
reachability; separately reproduce the application's schema-tag selection using
httpxgen's supported tag metadata/configuration.

## Expected behavior

1. Accept and validate supported OpenAPI 3.2 documents while allowing ordinary
   REST generation to exclude SSE operations.
2. Follow schema references through Media Type Object `itemSchema` and JSON
   Schema `contentSchema` during model discovery and selection. Keep nested and
   recursive references reachable. Filtering out an SSE method should not make
   explicitly selected event models unavailable.
3. Keep SSE transport generation optional. This request needs correct contract
   acceptance and shared models; it does not require httpxgen to implement an SSE
   runtime or take over reconnect/replay behavior.
4. Test mixed REST/SSE documents, model selection, unchanged REST output and clear
   diagnostics for unsupported OpenAPI 3.2 features.

## Temporary consumer workaround

Keep a single authoritative OpenAPI 3.2 artifact. Generate the standalone SSE SDK
directly from it. Derive a private REST-codegen view for a generator limited to
3.1, retaining event-model references, then generate/check the HTTP client from
that derived file. Never publish the private view or edit it as a second contract.

Canon provides a tested, deliberately scoped example at
`packages/fastapi-streams/examples/rest_codegen.py`, documented in
`packages/fastapi-streams/docs/native-transports.md`. It replaces inline JSON SSE
`itemSchema` with a private media `schema` representing decoded event data for
model discovery. This is not the SSE wire body or a universal 3.2-to-3.1 converter;
filter those operations out of ordinary HTTP method generation.

## HTTP backend choice is separate

`httpx` and `httpx2` are selectable HTTP backends for the generated Streams Python
SDK. Choosing HTTPX2 does not fix httpxgen's contract parsing or model discovery.
Keep the application's existing backend unless it has a concrete reason to
change. If choosing HTTPX2, pass `--python-http-client httpx2` to both generation
and drift checks and install only that selected backend with Pydantic.

The high-level consumer can continue owning native transport, authentication,
run identity and recovery. Reuse the standalone SDK only where its validated
contract and explicit unknown-event policy match that consumer's needs.
