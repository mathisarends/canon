import asyncio
from collections.abc import Callable
from enum import StrEnum
from typing import Self

from fastapi_rpckit._activity import _Activity, notify_activity
from fastapi_rpckit.connection import (
    RpcConnection,
    RpcConnectionClose,
    RpcDisconnect,
    RpcLimits,
    RpcWebSocket,
)


class RpcMessageType(StrEnum):
    TEXT = "text"
    BINARY = "binary"


type RpcSocketMessage = str | bytes


class RpcSocket:
    """An accepted WebSocket that passes text and binary messages through as-is.

    Iteration ends when the connection closes. fastapi_rpckit cancels the handler when
    the client disconnects or the connection closes, so ``finally`` blocks and
    context managers release upstream resources.
    """

    __slots__ = (
        "_connection",
        "_disconnected",
        "_lock",
        "_messages",
        "_activity",
        "_queue",
        "_request_close",
        "_send_timeout",
        "_socket",
    )

    def __init__(self) -> None:
        raise TypeError("RpcSocket instances are created by fastapi_rpckit")

    @classmethod
    def _create(
        cls,
        socket: RpcWebSocket,
        connection: RpcConnection,
        messages: tuple[RpcMessageType, ...],
        limits: RpcLimits,
        activity: _Activity | None,
        request_close: Callable[[RpcConnectionClose, str], None],
        disconnected: Callable[[RpcDisconnect], None],
    ) -> Self:
        self = cls.__new__(cls)
        self._socket = socket
        self._connection = connection
        self._messages = messages
        self._activity = activity
        self._send_timeout = limits.send_timeout
        self._queue = asyncio.Queue[RpcSocketMessage](limits.max_queue_size)
        self._lock = asyncio.Lock()
        self._request_close = request_close
        self._disconnected = disconnected
        return self

    @property
    def messages(self) -> tuple[RpcMessageType, ...]:
        """The message types this endpoint declared."""
        return self._messages

    @property
    def closed(self) -> bool:
        return self._connection.closed or self._connection.close_code is not None

    async def receive(self) -> RpcSocketMessage:
        """Wait for the next client message; ``str`` is text, ``bytes`` binary."""
        if self.closed and self._queue.empty():
            raise RpcDisconnect(
                self._connection.close_code or RpcConnectionClose.NORMAL,
                self._connection.close_reason,
            )
        return await self._queue.get()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> RpcSocketMessage:
        try:
            return await self.receive()
        except RpcDisconnect:
            raise StopAsyncIteration from None

    async def send(self, message: str | bytes | bytearray | memoryview) -> None:
        """Send a text (``str``) or binary message; waits on socket backpressure."""
        if isinstance(message, str):
            message_type = RpcMessageType.TEXT
        elif isinstance(message, bytes | bytearray | memoryview):
            message_type = RpcMessageType.BINARY
        else:
            raise TypeError("RpcSocket.send() expects str or bytes")
        if message_type not in self._messages:
            raise TypeError(f"This socket does not send {message_type} messages")
        async with self._lock:
            if self.closed:
                raise RpcDisconnect(reason="The socket is closed")
            try:
                async with asyncio.timeout(self._send_timeout):
                    if isinstance(message, str):
                        await self._socket.send(message)
                        size = len(message.encode())
                    else:
                        data = bytes(message)
                        await self._socket.send_bytes(data)
                        size = len(data)
            except RpcDisconnect as error:
                self._disconnected(error)
                raise
            except TimeoutError:
                self._request_close(
                    RpcConnectionClose.POLICY_VIOLATION, "Client too slow"
                )
                await notify_activity(
                    self._activity, "slow_consumer_closed", self._connection
                )
                raise RpcDisconnect(
                    RpcConnectionClose.POLICY_VIOLATION, "Client too slow"
                ) from None
        await notify_activity(
            self._activity, "stream_frame_sent", self._connection, size
        )

    async def close(
        self,
        close: RpcConnectionClose = RpcConnectionClose.NORMAL,
        *,
        reason: str = "",
    ) -> None:
        """Close the connection and cancel its handler."""
        await self._connection.close(close, reason=reason)

    async def _put(self, message: RpcSocketMessage) -> None:
        await self._queue.put(message)
