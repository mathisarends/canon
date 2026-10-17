import {
  HttpError, isHttpError, StreamParseError, TransportError,
  type Client, type RequestOptions, type StreamRunEventsErrorBody,
} from "./generated/index.js";

export async function consumeWithErrors(
  client: Client,
  runId: string,
  options: RequestOptions = {},
): Promise<void> {
  try {
    for await (const event of client.agentRuns.streamRunEvents({ runId }, options)) {
      if (event.type === "run.failed") console.error(event.message);
      else console.log(event);
    }
  } catch (error: unknown) {
    if (options.signal?.aborted) throw error;
    if (isHttpError(error, isValidationErrorBody) && error.status === 422) {
      console.error("Invalid stream parameters", error.details.detail ?? []);
      return;
    }
    if (error instanceof HttpError) {
      console.error("Unexpected HTTP response", error.status, error.details);
    } else if (error instanceof StreamParseError) {
      console.error("Invalid event JSON", error.data);
    } else if (error instanceof TransportError) {
      console.error("Stream transport failed", error.message);
    }
    throw error;
  }
}

function isValidationErrorBody(value: unknown): value is StreamRunEventsErrorBody {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  if (!("detail" in value)) return true;
  return Array.isArray(value.detail) && value.detail.every((item: unknown) => {
    if (typeof item !== "object" || item === null || Array.isArray(item)) return false;
    return "loc" in item && Array.isArray(item.loc)
      && item.loc.every((part: unknown) => typeof part === "string"
        || (typeof part === "number" && Number.isInteger(part)))
      && "msg" in item && typeof item.msg === "string"
      && "type" in item && typeof item.type === "string";
  });
}
