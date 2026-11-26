# Stage 3 MQTT feasibility evidence

Measured on 2026-11-26. These are small, bounded, real-connection feasibility results, not the project's capacity acceptance tests.

## Configuration

- Apple Silicon ARM64 host; 16 GiB RAM and 10 logical CPUs observed during setup.
- Docker Engine 29.9.3, VM approximately 7.75 GiB RAM / 10 CPUs during this stage.
- Broker: Mosquitto 2.0.22, image digest `sha256:81a6193ae693942a3231cd3ac52875b02b7e3a19da671b2fb4b55cc874c5b279`, 256 MiB / 1 CPU container limit.
- Python 3.14.7, Paho 2.2.0; exact application/dev dependencies are in uv.lock.
- Experiment implementation commit: `e8bae7c` (full history in this repository).
- MQTT 5 / QoS 1, anonymous plaintext loopback only, three self-echo rounds per client.
- Broker session expiry: 60 seconds; disk persistence disabled for this disposable harness.
- One metrics-observer connection in addition to the reported workload clients.

## Results

| Actual workload clients | Broker connected count | Verified deliveries | Connect/ramp time | Burst p95 round trip | Sampled client RSS | Client threads |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 11 | 30 | 0.433 s | 7.93 ms | 31.61 MiB | 1 |
| 100 | 101 | 300 | 1.582 s | 12.84 ms | 31.91 MiB | 1 |
| 1,000 | 1,001 | 3,000 | 15.279 s | 159.34 ms | 57.77 MiB | 1 |

Machine-readable records: [10 clients](mqtt-10.json), [100 clients](mqtt-100.json), [1,000 clients](mqtt-1000.json). Each reports measured duration, process CPU, versions and limitations. The short burst throughput fields should not be used as sustained platform throughput estimates. RSS samples are taken after connects and rounds, not continuous memory profiling; broker and Docker memory are excluded from client RSS.

## Acknowledgement evidence

The real-broker tests prove an unacknowledged QoS 1 message is redelivered with the same packet identifier and duplicate flag after persistent-session resume. After explicit ACK, the message is absent on a later resumed session. A separate profile test verifies ten simultaneous clients, twenty deliveries and zero added process threads.

## Conclusion and limits

Paho external-loop integration is feasible for the next local implementation slice at the measured scale. Retain it as the candidate; re-evaluate with per-device TLS and realistic publishing intervals before expanding the claim.

This run does **not** validate 25,000–50,000 connections, TLS handshake memory, per-device certificates, reconnect storms, sustained heartbeat traffic, Redis/PostgreSQL delivery, commit receipts, database deduplication, broker persistence or high availability. The 1,000-client measured burst lasted about half a second after ramp-up. There is no extrapolation from that burst to production capacity.

See [development instructions](../development.md) for reproduction and cleanup. All Stage 4 and later runtime acceptance criteria remain pending.

## Final Stage 3 checks

All 88 tests passed in the development environment and again in a fresh non-editable installation from uv.lock (4.13 seconds for the clean-install suite). The second run checked the installed package under site-packages, not an editable source import. The lockfile hash was unchanged. Ruff lint/format checks passed and wheel/source distributions built successfully. The disposable broker container and Compose network were removed afterward.
