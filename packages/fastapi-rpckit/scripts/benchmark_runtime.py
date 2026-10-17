import argparse
import asyncio
import importlib
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path


async def measure(operation, iterations, rounds):
    for _ in range(100):
        await operation()
    wall, cpu = [], []
    for _ in range(rounds):
        started = time.perf_counter_ns()
        cpu_started = time.process_time_ns()
        for _ in range(iterations):
            await operation()
        cpu.append((time.process_time_ns() - cpu_started) / iterations / 1000)
        wall.append((time.perf_counter_ns() - started) / iterations / 1000)
    return {
        "iterations_per_round": iterations,
        "median_us": statistics.median(wall),
        "cpu_median_us": statistics.median(cpu),
        "samples_us": wall,
        "cpu_samples_us": cpu,
    }


async def benchmark(source_dir, output_dir, rounds):
    # Import only after selecting the checkout, using the same interpreter and
    # dependencies for all revisions under comparison.
    sys.path.insert(0, str(source_dir))
    from pydantic import BaseModel, TypeAdapter

    import fastapi_rpckit
    from fastapi_rpckit import RpcChannel, RpcDisconnect, RpcHandshake, RpcService
    from fastapi_rpckit.codegen import generate_python_client
    from fastapi_rpckit.codegen.python import PythonClientOptions
    from fastapi_rpckit.schema import render_openrpc

    channel = RpcChannel("bench")

    class Params(BaseModel):
        values: list[int]

    @channel.method()
    async def work() -> int:
        return 1

    @channel.method()
    async def payload(params: Params) -> int:
        return len(params.values)

    class Socket:
        handshake = RpcHandshake(path="/rpc", headers={}, query_params={})

        def __init__(self):
            self.incoming = asyncio.Queue()
            self.outgoing = asyncio.Queue()

        async def accept(self, subprotocol=None): ...

        async def reject(self, *args, **kwargs): ...

        async def receive(self):
            value = await self.incoming.get()
            if value is None:
                raise RpcDisconnect()
            return value

        async def send(self, message):
            self.outgoing.put_nowait(message)

        async def send_bytes(self, data): ...

        async def close(self, *args): ...

    class Transport:
        async def request(self, method, params=None, **kwargs):
            return 1

        async def close(self): ...

        async def notifications(self):
            if False:
                yield {}

    results = {
        "source": str(source_dir),
        "imported_from": fastapi_rpckit.__file__,
        "python": sys.version,
        "rounds": rounds,
    }
    server = channel.create_server()
    message = {"jsonrpc": "2.0", "id": 1, "method": "bench.work"}
    results["server_handle"] = await measure(
        lambda: server.handle(message), 20000, rounds
    )
    frame = json.dumps(message)
    results["server_handle_json"] = await measure(
        lambda: server.handle_json(frame), 10000, rounds
    )
    service = RpcService()
    service.socket("/rpc", channels=[channel])
    socket = Socket()
    serving = asyncio.create_task(service.serve(socket))

    async def roundtrip():
        await socket.incoming.put(frame)
        await socket.outgoing.get()

    try:
        results["socket_roundtrip"] = await measure(roundtrip, 5000, rounds)
    finally:
        socket.incoming.put_nowait(None)
        await serving

    generate_python_client(
        render_openrpc(channel.protocol, title="Bench"),
        output_dir / "bench_sdk",
        PythonClientOptions(package="bench_sdk"),
    )
    sys.path.insert(0, str(output_dir))
    runtime = importlib.import_module("bench_sdk.internal.core")
    metadata = importlib.import_module("bench_sdk.internal.metadata")
    models = importlib.import_module("bench_sdk.models")
    core = runtime.RpcClientCore(Transport())
    try:
        for size in (0, 10, 10000):
            extra = {}
            if size and "params_adapter" in metadata.RpcRouteInfo.__dataclass_fields__:
                extra["params_adapter"] = TypeAdapter(models.Params)
            route = metadata.RpcRouteInfo(
                method="bench.payload" if size else "bench.work",
                result_adapter=TypeAdapter(int),
                **extra,
            )
            params = models.Params(values=list(range(size))) if size else None
            results[f"sdk_{size}_ints"] = await measure(
                lambda route=route, params=params: core.request(route, params=params),
                1000 if size == 10000 else 20000,
                rounds,
            )
    finally:
        await core.close()
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Measure local CPU overhead without network I/O. Run revisions "
        "sequentially on an idle machine; compare samples as well as medians."
    )
    parser.add_argument(
        "--source-dir", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=7)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    with tempfile.TemporaryDirectory(prefix="fastapi_rpckit-benchmark-") as directory:
        results = asyncio.run(
            benchmark(args.source_dir.resolve(), Path(directory), args.rounds)
        )
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
