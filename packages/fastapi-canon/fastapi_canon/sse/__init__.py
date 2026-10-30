from typing import TYPE_CHECKING, Any

from fastapi_canon._version import __version__

if TYPE_CHECKING:
    from fastapi_canon.sse.router import StreamRouter as StreamRouter

__all__ = ["StreamRouter", "__version__"]


def __getattr__(name: str) -> Any:
    if name == "StreamRouter":
        from fastapi_canon.sse.router import StreamRouter

        return StreamRouter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
