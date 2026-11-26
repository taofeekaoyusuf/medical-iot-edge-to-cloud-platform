"""Measure a capped localhost profile; never extrapolate this result to production.

Usage: uv run --locked python -m experiments.mqtt_clients --clients 100
"""

import argparse
import asyncio
import json
import math
import platform
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import psutil

from experiments.mqtt_client import LocalClient


async def run_profile(clients: int, rounds: int = 3) -> dict:
    if type(clients) is not int or not 1 <= clients <= 1000:
        raise ValueError("clients must be an integer in 1..1000")
    if type(rounds) is not int or not 1 <= rounds <= 20:
        raise ValueError("rounds must be an integer in 1..20")
    process = psutil.Process()
    baseline_threads = process.num_threads()
    peak_threads = baseline_threads
    peak_rss = process.memory_info().rss
    start_cpu = sum(process.cpu_times()[:2])
    start = time.perf_counter()
    connected = []
    prefix = uuid4().hex[:12]
    observer = LocalClient(f"observer-{prefix}")
    latencies = []

    def sample():
        nonlocal peak_rss, peak_threads
        peak_rss = max(peak_rss, process.memory_info().rss)
        peak_threads = max(peak_threads, process.num_threads())
        if peak_rss > 512 * 1024 * 1024:
            raise RuntimeError("Client process exceeded the experiment's 512 MiB RSS ceiling")

    try:
        await observer.connect()
        await observer.subscribe("$SYS/broker/clients/connected")
        for index in range(clients):
            client = LocalClient(f"probe-{prefix}-{index}")
            connected.append(client)  # Include failed connects in cleanup.
            await client.connect()
            await client.subscribe(f"stage3/{prefix}/{index}")
            sample()
            await asyncio.sleep(0.01)  # At most 100 new clients/second.
        connect_seconds = time.perf_counter() - start
        broker_count = 0
        # The independent broker metric confirms these are sockets, not just identities.
        async with asyncio.timeout(10):
            while broker_count < clients + 1:
                broker_count = int((await observer.receive()).payload)
        connected_count = sum(client.connected for client in connected)
        if connected_count != clients:
            raise RuntimeError("A client disconnected before the measured rounds")

        async def exchange(index, client, round_index):
            payload = f"{prefix}:{index}:{round_index}".encode()
            started = time.perf_counter()
            await client.publish(f"stage3/{prefix}/{index}", payload)
            message = await client.receive()
            if message.payload != payload:
                raise RuntimeError("Unexpected or duplicated experiment payload")
            latencies.append(time.perf_counter() - started)

        measurement_start = time.perf_counter()
        for round_index in range(rounds):
            await asyncio.gather(
                *(exchange(index, client, round_index) for index, client in enumerate(connected))
            )
            sample()
        measurement_seconds = time.perf_counter() - measurement_start
        if not all(client.connected for client in connected):
            raise RuntimeError("A client disconnected during the measured rounds")
        ordered = sorted(latencies)
        return {
            "recorded_at": datetime.now(UTC).isoformat(),
            "transport": "plaintext-loopback",
            "python_version": platform.python_version(),
            "paho_version": version("paho-mqtt"),
            "architecture": platform.machine(),
            "configured_clients": clients,
            "connected_clients": connected_count,
            "broker_connected_clients": broker_count,
            "observer_connections": 1,
            "rounds": rounds,
            "verified_deliveries": len(latencies),
            "connect_seconds": round(connect_seconds, 4),
            "measurement_seconds": round(measurement_seconds, 4),
            "verified_deliveries_per_second": round(len(latencies) / measurement_seconds, 2),
            "roundtrip_p95_seconds": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 6),
            "sampled_peak_rss_bytes": peak_rss,
            "baseline_threads": baseline_threads,
            "sampled_peak_threads": peak_threads,
            "new_threads": peak_threads - baseline_threads,
            "process_cpu_seconds": round(sum(process.cpu_times()[:2]) - start_cpu, 4),
            "limitations": (
                "Short plaintext self-echo bursts; no TLS, database, HA or sustained-load claim"
            ),
        }
    finally:
        # Wait for every close even if one connection fails, avoiding leaked local sockets.
        results = await asyncio.gather(
            *(client.close() for client in [*connected, observer]),
            return_exceptions=True,
        )
        errors = [result for result in results if isinstance(result, Exception)]
        if errors:
            raise RuntimeError("One or more experiment sockets failed to close") from errors[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = asyncio.run(run_profile(args.clients, args.rounds))
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
