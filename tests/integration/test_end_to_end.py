import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from examples.agent_runs.generated_python import Client
from examples.agent_runs.generated_python.models import RunRequest

ROOT = Path(__file__).parents[2]


@pytest.fixture(scope="module")
def server():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "examples.agent_runs:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        with httpx.Client(trust_env=False) as client:
            for _ in range(100):
                if process.poll() is not None:
                    pytest.fail(process.communicate()[1].decode())
                try:
                    if client.get(url + "/health", timeout=0.2).is_success:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.05)
            else:
                pytest.fail("Example server did not become ready")
        yield url
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def test_generated_typescript_client_over_real_http(server):
    node = shutil.which("node")
    compiler = ROOT / "node_modules/typescript/bin/tsc"
    if not node or not compiler.exists():
        pytest.skip("Run npm ci to enable the TypeScript end-to-end acceptance test")
    subprocess.run(
        [node, str(compiler), "-p", "tests/typescript/tsconfig.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    result = subprocess.run(
        [node, "tests/typescript/dist/tests/typescript/live-client.js", server],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert "generated Fetch client: passed" in result.stdout


async def test_generated_python_client_over_real_http(server):
    async with Client(server, headers={"Authorization": "Bearer demo-token"}) as client:
        events = [
            event
            async for event in client.agent_runs.stream_run_events(
                run_id="python", delay=0
            )
        ]
        assert events[0].type == "run.started"
        assert events[-1].type == "run.completed"
        assert (
            "".join(event.text for event in events if event.type == "token.delta")
            == "Hello 世界 👋"
        )
        events = [
            event
            async for event in client.agent_runs.stream_prompt(
                run_id="python", body=RunRequest(prompt="typed python")
            )
        ]
        assert len([event for event in events if event.type == "token.delta"]) == 2
