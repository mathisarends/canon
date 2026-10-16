import asyncio

from examples.agent_runs.generated_python import Client


async def main() -> None:
    async with Client(
        "http://127.0.0.1:8000", headers={"Authorization": "Bearer demo-token"}
    ) as client:
        async for event in client.agent_runs.stream_run_events(run_id="demo"):
            match event.type:
                case "run.started":
                    print(f"Started {event.run_id}")
                case "token.delta":
                    print(event.text, end="", flush=True)
                case "run.completed":
                    print(f"\nCompleted {event.run_id}")
                case "run.failed":
                    print(event.message)


if __name__ == "__main__":
    asyncio.run(main())
