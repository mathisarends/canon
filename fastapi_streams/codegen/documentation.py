from typing import Literal

from fastapi_streams.codegen.ir import Operation
from fastapi_streams.codegen.names import identifier


def operation_doc(
    operation: Operation, language: Literal["typescript", "python"]
) -> str:
    """Combine endpoint descriptions with guarantees of the selected SDK."""
    paragraphs = [part for part in (operation.summary, operation.description) if part]
    paragraphs.extend(
        [
            f"HTTP {operation.method} {operation.path}.",
            "Opens the HTTP request when iteration begins. "
            "Parameter and body preparation may fail at the method call.",
            "Does not automatically reconnect, retry, or replay events.",
            "HTTP failures raise HttpError; reading or decoding failures raise "
            "TransportError or StreamParseError. Application error events "
            "remain events.",
        ]
    )
    if operation.errors:
        name = identifier(operation.operation_id, upper=True) + "ErrorBody"
        responses = "; ".join(
            sorted({f"{error.status} {error.media_type}" for error in operation.errors})
        )
        paragraphs.append(
            f"Declared HTTP response bodies: {name} ({responses}). "
            "HttpError.details may also contain undeclared JSON, text, or no body; "
            "validate it before accessing application fields."
        )
    if language == "typescript":
        paragraphs.extend(
            [
                "Breaking iteration closes the reader and aborts the request. "
                "Caller cancellation propagates the AbortSignal reason.",
                "Events are JSON-decoded with static types; their schemas "
                "are not validated at runtime.",
            ]
        )
    else:
        paragraphs.extend(
            [
                "Use contextlib.aclosing for deterministic cleanup when exiting "
                "iteration early. Task cancellation closes the response and "
                "propagates normally.",
                "Events are validated with Pydantic.",
            ]
        )
    if operation.deprecated:
        paragraphs.append(
            "@deprecated" if language == "typescript" else "Deprecated endpoint."
        )
    text = "\n\n".join(paragraphs)
    # Prevent endpoint prose from terminating or changing generated source strings.
    if language == "typescript":
        return text.replace("*/", "*\\/")
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\x00", "\\x00")
