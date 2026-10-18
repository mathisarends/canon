import json
from typing import Annotated, Literal

import httpx
import pytest
from pydantic import BaseModel, Field

from fastapi_streams.codegen.python import generate_python
from tests.codegen.helpers import event_contract, load_package


class Started(BaseModel):
    type: Literal["started"]
    run_id: str


class Done(BaseModel):
    type: Literal["done"]
    count: int


type Event = Annotated[Started | Done, Field(discriminator="type")]


@pytest.mark.parametrize("backend", ["httpx", "httpx2"])
@pytest.mark.parametrize(
    ("policy", "payloads", "expected"),
    [
        ("error", [{"type": "future"}], "error"),
        ("ignore", [{"type": "future"}, {"type": "done", "count": 1}], "done"),
        ("ignore", [{"type": "started"}], "error"),
        ("ignore", [{"count": 1}], "error"),
        ("ignore", [{"type": 5}], "error"),
        ("ignore", ["broken-json"], "error"),
    ],
)
async def test_unknown_policy_preserves_known_validation(
    tmp_path, backend, policy, payloads, expected
):
    if backend == "httpx2":
        import httpx2 as http
    else:
        http = httpx

    content = "".join(
        "data: " + (p if isinstance(p, str) else json.dumps(p)) + "\n\n"
        for p in payloads
    )
    with load_package(
        tmp_path / "sdk", generate_python(event_contract(Event), http_client=backend)
    ) as sdk:
        async with (
            http.AsyncClient(
                transport=http.MockTransport(
                    lambda _: http.Response(
                        200,
                        content=content,
                        headers={"content-type": "text/event-stream"},
                    )
                )
            ) as client,
            sdk.Client("http://example.test", http_client=client) as api,
        ):
            events = api.streams.events(
                options=sdk.RequestOptions(unknown_events=policy)
            )
            if expected == "error":
                with pytest.raises(sdk.StreamParseError):
                    await anext(events)
            else:
                result = [event async for event in events]
                assert len(result) == 1 and result[0].type == expected


async def test_ignore_requires_a_discriminated_union(tmp_path):
    with load_package(tmp_path / "sdk", generate_python(event_contract(str))) as sdk:
        async with sdk.Client("http://example.test") as api:
            with pytest.raises(ValueError, match="top-level discriminated"):
                await anext(
                    api.streams.events(
                        options=sdk.RequestOptions(unknown_events="ignore")
                    )
                )
