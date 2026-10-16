import { createClient } from "./generated/index.js";

const client = createClient({
  baseUrl: "http://127.0.0.1:8000",
  headers: { Authorization: "Bearer demo-token" },
});

for await (const event of client.agentRuns.streamRunEvents({ runId: "demo" })) {
  switch (event.type) {
    case "run.started":
      console.log(`Started ${event.run_id}`);
      break;
    case "token.delta":
      process.stdout.write(event.text);
      break;
    case "run.completed":
      console.log(`\nCompleted ${event.run_id}`);
      break;
    case "run.failed":
      console.error(event.message);
      break;
    default: {
      const exhaustive: never = event;
      throw new Error(`Unexpected event: ${exhaustive}`);
    }
  }
}
