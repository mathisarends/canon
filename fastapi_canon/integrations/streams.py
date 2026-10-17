"""Canon error contracts for typed fastapi-streams endpoints."""

try:
    from fastapi_streams import StreamRouter
except ModuleNotFoundError as exc:
    if exc.name != "fastapi_streams":
        raise
    msg = "CanonStreamRouter requires fastapi-streams; install fastapi-canon[streams]"
    raise ModuleNotFoundError(msg, name=exc.name) from exc

from fastapi_canon.router import CanonRouter

__all__ = ["CanonStreamRouter"]


class CanonStreamRouter(CanonRouter, StreamRouter):
    """Combine canon contracts with native typed GET/POST SSE generators.

    StreamRouter.stream() registers through CanonRouter.api_route(), preserving
    canon's registry validation, shared/local raises, and contract compilation.
    Feature discovers the registry through the CanonRouter base class.

    Run HTTP preconditions in dependencies. Even code before a generator's first
    yield runs after the response starts. ``raises=`` documents HTTP failures;
    errors during streaming need an application-specific event protocol.
    """
