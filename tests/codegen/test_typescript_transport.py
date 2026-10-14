import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest

from rpckit.codegen import generate_typescript_client
from rpckit.codegen.typescript import TypeScriptClientOptions


def test_transport_resilience_in_node(document: dict[str, Any], tmp_path: Path) -> None:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    node = shutil.which("node.exe") or shutil.which("node")
    if npx is None or node is None:
        pytest.skip("Node.js and npx are required")
    deployed = deepcopy(document)
    deployed["servers"] = [
        {
            "name": "rpc",
            "url": "ws://test",
            "x-rpckit-transport": {"type": "websocket", "messageEncoding": "json"},
        }
    ]
    generate_typescript_client(
        deployed,
        tmp_path / "generated",
        TypeScriptClientOptions(with_transport="websocket"),
    )
    runner = tmp_path / "transport.test.ts"
    runner.write_text(
        dedent(
            """
            import { WebSocketTransport } from "./generated/transport";

            function assert(value: unknown, message: string): asserts value {
              if (!value) throw new Error(message);
            }

            class Socket {
              readyState = 1;
              sent: Record<string, unknown>[] = [];
              listeners = new Map<string, ((event: { data: unknown }) => void)[]>();
              addEventListener(
                type: string, listener: (event: { data: unknown }) => void,
              ) {
                const listeners = this.listeners.get(type) ?? [];
                this.listeners.set(type, [...listeners, listener]);
              }
              send(data: string) { this.sent.push(JSON.parse(data)); }
              close() { this.readyState = 3; }
              receive(message: object) {
                for (const listener of this.listeners.get("message") ?? []) {
                  listener({ data: JSON.stringify({ jsonrpc: "2.0", ...message }) });
                }
              }
            }

            async function main() {
              const set = globalThis.setTimeout;
              const clear = globalThis.clearTimeout;
              const timers = new Map<number, () => void>();
              let next = 1;
              globalThis.setTimeout = ((callback: () => void) => {
                const id = next++;
                timers.set(id, callback);
                return id;
              }) as typeof setTimeout;
              globalThis.clearTimeout = ((id: number) => {
                timers.delete(id);
              }) as typeof clearTimeout;
              try {
                const socket = new Socket();
                const transport = await WebSocketTransport.open("ws://test", {
                  socketFactory: () => socket,
                });
                const slow = transport.request("slow").then(
                  () => { throw new Error("slow call unexpectedly succeeded"); },
                  error => assert(String(error).includes("timed out"), "wrong timeout"),
                );
                const [timer, expire] = [...timers.entries()][0];
                timers.delete(timer);
                expire();
                await slow;
                const other = transport.request("other");
                socket.receive({ id: 1, result: "late" });
                socket.receive({ id: 999, error: { code: -1, message: "unknown" } });
                socket.receive({ id: 2, result: "ok" });
                socket.receive({ id: 2, result: "duplicate" });
                assert(await other === "ok", "late response killed another call");
                assert(socket.readyState === 1, "socket closed on late response");

                socket.receive({ id: "server:1", method: "room.ping" });
                const answer = socket.sent.at(-1)!;
                assert(answer.id === "server:1", "wrong server request id");
                assert(JSON.stringify(answer.error) === JSON.stringify({
                  code: -32601,
                  message: "Method not found",
                  data: { code: "method_not_found", details: { method: "room.ping" } },
                }), "wrong client-method error");
                const later = transport.request("later");
                socket.receive({ id: 3, result: "alive" });
                assert(await later === "alive", "client method killed transport");
                await transport.close();
                assert(timers.size === 0, "timers leaked after close");

                for (const invalid of [
                  { id: "bad", result: 1 },
                  { id: true, result: 1 },
                  { id: 999 },
                  { id: 999, result: 1, error: { code: -1, message: "bad" } },
                  { id: 999, error: "bad" },
                  { id: 999, error: { code: "bad", message: "bad" } },
                ]) {
                  const badSocket = new Socket();
                  const bad = await WebSocketTransport.open("ws://test", {
                    socketFactory: () => badSocket,
                  });
                  const call = bad.request("pending").then(
                    () => { throw new Error("malformed response accepted"); },
                    error => assert(error instanceof Error, "wrong protocol failure"),
                  );
                  badSocket.receive(invalid);
                  await call;
                  assert(badSocket.readyState === 3, "malformed response kept open");
                  assert(timers.size === 0, "failure leaked a request timer");
                }
              } finally {
                globalThis.setTimeout = set;
                globalThis.clearTimeout = clear;
              }
            }
            void main();
            """
        ),
        encoding="utf-8",
    )
    compiled = tmp_path / "compiled"
    checked = subprocess.run(
        [
            npx,
            "--yes",
            "--package",
            "typescript",
            "tsc",
            "--strict",
            "--target",
            "ES2022",
            "--module",
            "Node16",
            "--moduleResolution",
            "Node16",
            "--lib",
            "ES2022,DOM,ESNext.Disposable",
            "--skipLibCheck",
            "--outDir",
            str(compiled),
            str(runner),
        ],
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    result = subprocess.run(
        [node, str(compiled / "transport.test.js")], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
