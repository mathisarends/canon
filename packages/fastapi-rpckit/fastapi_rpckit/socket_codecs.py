import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from pydantic import TypeAdapter
from pydantic_core import SchemaValidator
from typing_extensions import TypeForm


class RpcMessageType(StrEnum):
    TEXT = "text"
    BINARY = "binary"


type RpcSocketMessage = str | bytes


class RpcSocketCodecError(ValueError):
    """A codec rejected a message; its details are never sent to the peer."""


@dataclass(frozen=True, slots=True, init=False)
class RpcSocketCodec[IncomingT, OutgoingT](ABC):
    """A reusable, synchronous wire codec with directional Pydantic contracts.

    Implement ``decode`` and ``encode`` using the cached adapters and output
    validator. Instances are shared across connections and must be stateless.
    Raise ``RpcSocketCodecError`` for malformed wire data. Unexpected exceptions
    are treated as implementation failures, not as invalid client input.
    """

    incoming_type: TypeForm[IncomingT]
    outgoing_type: TypeForm[OutgoingT]
    incoming: TypeAdapter[IncomingT]
    outgoing: TypeAdapter[OutgoingT]
    name: str
    encoding: str
    message_types: tuple[RpcMessageType, ...]
    _output_validator: SchemaValidator

    def __init__(
        self,
        *,
        incoming: TypeForm[IncomingT],
        outgoing: TypeForm[OutgoingT],
        name: str,
        encoding: str,
        messages: Iterable[RpcMessageType],
    ) -> None:
        if incoming is Any or outgoing is Any:
            raise TypeError("Socket codecs need concrete incoming and outgoing types")
        for label, value in (("name", name), ("encoding", encoding)):
            if (
                not isinstance(value, str)
                or re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", value) is None
            ):
                raise ValueError(f"Socket codec {label} must be a lowercase token")
        frames = frozenset(RpcMessageType(value) for value in messages)
        if not frames:
            raise ValueError("Socket codecs need at least one message type")
        client, server = TypeAdapter(incoming), TypeAdapter(outgoing)
        client.json_schema()
        server.json_schema(mode="serialization")
        schema = deepcopy(server.core_schema)
        _revalidate_models(schema)
        for attribute, value in {
            "incoming_type": incoming,
            "outgoing_type": outgoing,
            "incoming": client,
            "outgoing": server,
            "name": name,
            "encoding": encoding,
            "message_types": tuple(item for item in RpcMessageType if item in frames),
            "_output_validator": SchemaValidator(schema),
        }.items():
            object.__setattr__(self, attribute, value)

    @abstractmethod
    def decode(self, message: RpcSocketMessage) -> IncomingT:
        """Decode and validate one complete text or binary message."""

    @abstractmethod
    def encode(self, message: OutgoingT) -> RpcSocketMessage:
        """Validate and encode one outgoing message without adding session state."""

    def validate_outgoing(self, message: OutgoingT) -> OutgoingT:
        """Revalidate existing model instances, including mutated fields."""
        return self._output_validator.validate_python(message, strict=True)


class RpcJsonCodec[IncomingT, OutgoingT](RpcSocketCodec[IncomingT, OutgoingT]):
    """Strict Pydantic validation and JSON text framing, with no RPC envelope."""

    def __init__(
        self, *, incoming: TypeForm[IncomingT], outgoing: TypeForm[OutgoingT]
    ) -> None:
        super().__init__(
            incoming=incoming,
            outgoing=outgoing,
            name="json",
            encoding="json",
            messages=(RpcMessageType.TEXT,),
        )

    def decode(self, message: RpcSocketMessage) -> IncomingT:
        if not isinstance(message, str):
            raise RpcSocketCodecError("JSON sockets require text messages")
        return self.incoming.validate_json(message, strict=True)

    def encode(self, message: OutgoingT) -> str:
        validated = self.validate_outgoing(message)
        return self.outgoing.dump_json(
            validated, by_alias=True, warnings="error"
        ).decode()


class RpcSocketCodecFactory(Protocol):
    """Create an endpoint codec from the handler's sole message-type declaration.

    A codec class with this constructor signature can be passed directly.
    Factories run once per endpoint declaration, never per message.
    """

    def __call__(
        self, *, incoming: TypeForm[Any], outgoing: TypeForm[Any]
    ) -> RpcSocketCodec[Any, Any]: ...


def _revalidate_models(value: Any) -> None:
    if isinstance(value, dict):
        if value.get("type") == "model":
            value["config"] = {
                **value.get("config", {}),
                "revalidate_instances": "always",
            }
        elif value.get("type") == "dataclass":
            value["revalidate_instances"] = "always"
        for child in value.values():
            _revalidate_models(child)
    elif isinstance(value, list | tuple):
        for child in value:
            _revalidate_models(child)
