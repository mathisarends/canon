from collections.abc import AsyncIterator, Iterator
from typing import Annotated, Any

import pytest
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from examples.agent_runs import app
from fastapi_streams import StreamRouter


class Event(BaseModel):
    value: str


def test_get_post_validation_auth_and_serialization():
    with TestClient(app) as client:
        response = client.get("/v1/runs/abc/events?delay=0")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert '"run_id":"abc"' in response.text
        assert "世界" in response.text
        assert response.headers["x-accel-buffering"] == "no"
        assert client.get("/v1/runs/abc/events?delay=-1").status_code == 422
        url = "/v1/runs/abc/events"
        assert client.post(url, json={"prompt": "Hello"}).status_code in (401, 403)
        headers = {"Authorization": "Bearer demo-token"}
        response = client.post(url, json={"prompt": "Hi there"}, headers=headers)
        assert response.status_code == 200
        assert '"text":"there"' in response.text
        assert client.post(url, json={"prompt": ""}, headers=headers).status_code == 422
        assert client.get("/health").json() == {"status": "ok"}


def test_nested_routers_dependencies_headers_and_cleanup():
    lifecycle = []

    def resource() -> Iterator[str]:
        lifecycle.append("open")
        try:
            yield "resource"
        finally:
            lifecycle.append("closed")

    def authorize(x_key: Annotated[str, Header()]) -> None:
        if x_key != "secret":
            raise HTTPException(403, "Denied")

    router = StreamRouter(prefix="/inner", dependencies=[Depends(authorize)])

    @router.stream("/{name}", operation_id="nested")
    async def events(
        name: str,
        resource: Annotated[str, Depends(resource)],
    ) -> AsyncIterator[Event]:
        assert lifecycle == ["open"]
        yield Event(value=f"{name}:{resource}")

    parent = APIRouter(prefix="/parent")
    parent.include_router(router)
    application = FastAPI()
    application.include_router(parent, prefix="/v1")
    with TestClient(application) as client:
        assert (
            client.get("/v1/parent/inner/a", headers={"x-key": "bad"}).status_code
            == 403
        )
        assert lifecycle == []
        response = client.get("/v1/parent/inner/a", headers={"x-key": "secret"})
        assert '"value":"a:resource"' in response.text
        assert lifecycle == ["open", "closed"]


def test_sync_generator():
    router = StreamRouter()

    @router.stream("/sync")
    def events() -> Iterator[Event]:
        yield Event(value="sync")

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        assert '"value":"sync"' in client.get("/sync").text


def test_invalid_annotations_and_options_fail_at_registration():
    router = StreamRouter()

    async def untyped():
        yield {}

    async def ambiguous() -> AsyncIterator[Any]:
        yield {}

    async def coroutine() -> Event:
        return Event(value="bad")

    for endpoint in (untyped, ambiguous, coroutine):
        with pytest.raises(TypeError):
            router.stream("/bad")(endpoint)
    with pytest.raises(ValueError, match="GET and POST"):
        router.stream("/bad", methods=["DELETE"])
    with pytest.raises(TypeError, match="infer"):
        router.stream("/bad", response_model=Event)
