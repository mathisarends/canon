import type { RunEvent, RunRequest } from "../../examples/agent_runs/generated/types.js";
import { createClient } from "../../examples/agent_runs/generated/index.js";

export function describe(event: RunEvent): string {
  switch (event.type) {
    case "run.started": return event.run_id;
    case "run.completed": return event.run_id;
    case "token.delta": {
      // @ts-expect-error Tokens have no run_id.
      event.run_id;
      return event.text;
    }
    case "run.failed": return event.message;
    default: {
      const unreachable: never = event;
      return unreachable;
    }
  }
}

const client = createClient({ baseUrl: "http://example.test" });
if (false) {
  // @ts-expect-error Path parameters are required.
  client.agentRuns.streamRunEvents({});
  // @ts-expect-error Path parameters preserve string types.
  client.agentRuns.streamRunEvents({ runId: 1 });
  // @ts-expect-error POST request bodies are required.
  client.agentRuns.streamPrompt({ runId: "a" });
}
export const validBody: RunRequest = { prompt: "Hello" };
