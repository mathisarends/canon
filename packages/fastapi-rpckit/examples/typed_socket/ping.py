from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from fastapi_rpckit import RpcChannel, RpcService, create_router


class Ping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["ping"] = "ping"
    value: int


class Pong(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["pong"] = "pong"
    value: int


messages = RpcChannel("messages")


@messages.method()
async def health() -> bool:
    return True


@messages.socket("ping")
async def ping(message: Ping) -> Pong:
    return Pong(value=message.value + 1)


service = RpcService()
service.socket("/rpc", channels=(messages,))
service.socket("/messages/ping", ping)
contract = service.contract(title="Typed Socket", base_url="ws://{host}")
app = FastAPI()
app.include_router(create_router(service))
