"""``WebRtcRouter``: declare session endpoints on a FastAPI router.

This module evaluates annotations eagerly: FastAPI reads the generated
endpoint signature, whose dependency refers to a closure-local factory.
"""

import asyncio
import inspect
import logging
import uuid
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypeVar, cast

from fastapi import APIRouter, Depends, WebSocket
from fastapi.params import Depends as DependsParam

from fastapi_webrtc.declarations import (
    DataChannelSpec,
    MediaPolicy,
    Role,
    Session,
    SessionDeclaration,
    SessionLimits,
)
from fastapi_webrtc.engine import Engine
from fastapi_webrtc.errors import ErrorCode, close_code
from fastapi_webrtc.events import EventHook, SessionEvent
from fastapi_webrtc.ice import IceServerSource
from fastapi_webrtc.runtime import RuntimeOptions, SessionRuntime

logger = logging.getLogger("fastapi_webrtc")

Factory = TypeVar("Factory", bound=Callable[..., Any])

DECLARATION_ATTRIBUTE = "__fastapi_webrtc__"


class _Counter:
    def __init__(self, limit: int | None) -> None:
        self.limit = limit
        self.active = 0

    @property
    def full(self) -> bool:
        return self.limit is not None and self.active >= self.limit


class _Slots:
    """Reserved capacity of one session in its router and endpoint counters."""

    def __init__(self, *counters: _Counter) -> None:
        self._counters = counters
        self._held = True
        for counter in counters:
            counter.active += 1

    def release(self) -> None:
        if self._held:
            self._held = False
            for counter in self._counters:
                counter.active -= 1


class WebRtcRouter(APIRouter):
    """An ``APIRouter`` whose ``session`` decorator declares WebRTC sessions.

    Each session is a WebSocket signaling endpoint. Its factory is a regular
    FastAPI dependency: path and query parameters, authentication and other
    dependencies resolve before the WebSocket is accepted, so a rejected
    request allocates no peer. Dependencies, including ``yield`` dependencies,
    stay open until the session's cleanup finished.

    Including the router in an application registers its lifespan, which closes
    every active session with ``shutdown`` when the application stops.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        ice_servers: IceServerSource | None = None,
        limits: SessionLimits | None = None,
        max_sessions: int | None = None,
        on_event: EventHook | None = None,
        prefix: str = "",
        tags: list[str] | None = None,
        dependencies: Sequence[DependsParam] | None = None,
    ) -> None:
        super().__init__(
            prefix=prefix,
            tags=list(tags or []),
            dependencies=list(dependencies or []),
            lifespan=self._lifespan,
        )
        if max_sessions is not None and max_sessions <= 0:
            raise ValueError("max_sessions must be positive")
        self.engine = engine
        self.ice_servers = ice_servers
        self.limits = limits or SessionLimits()
        self.event_hook = on_event
        self.declarations: list[SessionDeclaration] = []
        self._counter = _Counter(max_sessions)
        self._runtimes: set[SessionRuntime] = set()
        self._closing = False

    @property
    def active_sessions(self) -> int:
        return len(self._runtimes)

    def session(
        self,
        path: str,
        *,
        name: str | None = None,
        role: Role = Role.ANSWERER,
        media: MediaPolicy | None = None,
        data_channels: Sequence[DataChannelSpec] = (),
        limits: SessionLimits | None = None,
        max_sessions: int | None = None,
        dependencies: Sequence[DependsParam] | None = None,
    ) -> Callable[[Factory], Factory]:
        """Declare a session endpoint whose factory returns a :class:`Session`.

        The factory may be a function, coroutine function or generator
        dependency. ``name`` defaults to the factory name and becomes the
        generated client's method name.
        """

        def decorator(factory: Factory) -> Factory:
            declaration = SessionDeclaration(
                name=name or factory.__name__,
                path=self.prefix + path,
                role=role,
                media=media or MediaPolicy(),
                channels=tuple(data_channels),
                limits=limits or self.limits,
                max_sessions=max_sessions,
                description=inspect.getdoc(factory),
            )
            if any(d.name == declaration.name for d in self.declarations):
                raise ValueError(f"Session {declaration.name!r} is already declared")
            channel_names = {spec.name for spec in declaration.channels}
            self.declarations.append(declaration)
            counter = _Counter(max_sessions)

            async def endpoint(
                websocket: WebSocket,
                session: Annotated[Session, Depends(factory)],
            ) -> None:
                if not isinstance(cast(object, session), Session):
                    logger.error(
                        "Session factory %s returned %s instead of Session",
                        declaration.name,
                        type(session).__name__,
                    )
                    await _refuse(websocket, ErrorCode.HANDLER_FAILURE)
                    return
                unknown = set(session.on_message) - channel_names
                if unknown:
                    logger.error(
                        "Session %s has handlers for undeclared channels: %s",
                        declaration.name,
                        ", ".join(sorted(unknown)),
                    )
                    await _refuse(websocket, ErrorCode.HANDLER_FAILURE)
                    return
                await self._serve(declaration, counter, websocket, session)

            endpoint.__doc__ = factory.__doc__
            endpoint.__name__ = f"webrtc_session_{declaration.name}"
            setattr(endpoint, DECLARATION_ATTRIBUTE, declaration)
            self.add_api_websocket_route(
                path,
                endpoint,
                name=declaration.name,
                dependencies=dependencies,
            )
            return factory

        return decorator

    async def _serve(
        self,
        declaration: SessionDeclaration,
        counter: _Counter,
        websocket: WebSocket,
        session: Session,
    ) -> None:
        session_id = uuid.uuid4().hex
        if self._closing:
            await _refuse(websocket, ErrorCode.SHUTDOWN)
            return
        if self._counter.full or counter.full:
            self._emit(
                SessionEvent(
                    kind="rejected",
                    name=declaration.name,
                    session_id=session_id,
                    elapsed_seconds=0.0,
                    code=ErrorCode.SESSION_LIMIT,
                )
            )
            await _refuse(websocket, ErrorCode.SESSION_LIMIT)
            return
        runtime = SessionRuntime(
            declaration=declaration,
            options=RuntimeOptions(
                engine=self.engine,
                ice_servers=self.ice_servers,
                on_event=self.event_hook,
            ),
            websocket=websocket,
            session=session,
            session_id=session_id,
            slots=_Slots(self._counter, counter),
        )
        self._runtimes.add(runtime)
        try:
            await runtime.serve()
        finally:
            self._runtimes.discard(runtime)

    def _emit(self, event: SessionEvent) -> None:
        if self.event_hook is None:
            return
        try:
            self.event_hook(event)
        except Exception:
            logger.exception("Session event hook failed")

    async def aclose(self, timeout: float | None = None) -> None:
        """Close every active session with ``shutdown`` and wait for cleanup.

        New sessions are refused afterwards. ``timeout`` defaults to the largest
        configured shutdown deadline plus one second.
        """
        self._closing = True
        runtimes = list(self._runtimes)
        for runtime in runtimes:
            runtime.terminate(ErrorCode.SHUTDOWN)
        if not runtimes:
            return
        if timeout is None:
            timeout = 1 + max(
                runtime.declaration.limits.shutdown_timeout_seconds
                for runtime in runtimes
            )
        waiters = [asyncio.ensure_future(r.wait_finished()) for r in runtimes]
        _, pending = await asyncio.wait(waiters, timeout=timeout)
        for waiter in pending:
            waiter.cancel()
        if pending:
            logger.warning("%d WebRTC session(s) did not finish cleanup", len(pending))

    @asynccontextmanager
    async def _lifespan(self, _app: Any) -> AsyncIterator[None]:
        self._closing = False
        try:
            yield
        finally:
            await self.aclose()


async def _refuse(websocket: WebSocket, code: ErrorCode) -> None:
    """Accept only to deliver a categorized close code to the browser."""
    await websocket.accept(subprotocol=_subprotocol(websocket))
    await websocket.close(code=close_code(code), reason=code.value)


def _subprotocol(websocket: WebSocket) -> str | None:
    from fastapi_webrtc.protocol import SUBPROTOCOL

    offered = websocket.scope.get("subprotocols") or []
    return SUBPROTOCOL if SUBPROTOCOL in offered else None
