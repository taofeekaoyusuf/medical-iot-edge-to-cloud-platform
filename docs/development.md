# Stage 3 local development

Stage 3 implements a Python foundation, six named process scaffolds, strict telemetry validators and a capped MQTT experiment. Device registration, authenticated device connections, persistent telemetry, production simulator, health rules, notifications and the application API are not implemented yet.

## Setup and verification

Prerequisites: uv, Python 3.14.7 (recorded in `.python-version`), Docker Desktop and Docker Compose. `uv sync --locked` can download the interpreter if unavailable and installs the exact resolved package versions from `uv.lock`. Only the test broker image is required; no cloud credentials or accounts are used.

```sh
uv sync --locked
make lint
make test-unit
make broker-up
make test
make experiment
make broker-down
make build
```

Run from this repository's root. `make test-unit` explicitly deselects the MQTT integration tests; it is not the full acceptance check. `make test` runs every test and fails if the broker is absent. Use `make broker-down` after failures as well; no other project's containers or volumes are stopped. The test harness has no persistent volume, so its sessions disappear when removed.

The experiment broker is digest-pinned Mosquitto 2.0.22, exposed only at `127.0.0.1:18883`, with a 256 MiB container memory limit and one CPU. It deliberately permits anonymous plaintext traffic for protocol feasibility only. This is not a deployable device-authentication configuration. Stage 4 will add a separate TLS/certificate/ACL design implementation. Do not expose this harness on a public interface.

## Service structure

`src/medical_iot/service.py` provides a factory for gateway, registry, processor, health, notifications and api process scaffolds. For example:

```sh
MEDICAL_IOT_SERVICE=api uv run --locked uvicorn medical_iot.service:create_app --factory --host 127.0.0.1 --port 8000
```

`/health/live` returns 200 and the selected service name. `/health/ready` deliberately returns 503 with `domain_service_not_implemented`. There are no domain routes or workers. An invalid service name fails startup instead of silently selecting another service. The `MEDICAL_IOT_SERVICE` environment value selects a scaffold; it is not authorization.

## Event validation

The implementation lives in `src/medical_iot/contracts/events.py`, rather than the originally illustrative `packages/contracts/` path. A conventional installable `src` layout avoids importing source files accidentally when testing built distributions.

`validate_event(payload, expected_device_id=..., received_at=...)` accepts UTF-8 JSON bytes or text. It checks the 8 KiB byte limit, duplicate JSON keys, strict envelope/data models, canonical IDs, calendar timestamps and firmware consistency. The optional identity and clock checks require trusted caller values. Omitting received_at validates structure only; a future gateway must provide trusted ingress time and identity explicitly.

Errors expose stable reason codes through `EventValidationError.code`. Payload limits use `PAYLOAD_TOO_LARGE`; schema failures use `SCHEMA_INVALID`; identity and clock policy use the codes in the contract document. Numeric operational fields accept JSON integers or finite floats, but not strings or booleans. Validators do not perform database deduplication, cross-event sequence ordering, certificate authentication or registration checks.

`EVENT_ADAPTER` is the Pydantic discriminator for the four event types. Any generated JSON Schema needs supplemental validation for custom canonical-ID, timestamp and cross-field rules; do not treat schema generation alone as the full wire boundary. Status/receipt models remain for their owning later stages.

## Bounded MQTT experiment

```sh
uv run --locked python -m experiments.mqtt_clients --clients 10 --output artifacts/mqtt-10.json
uv run --locked python -m experiments.mqtt_clients --clients 100 --output artifacts/mqtt-100.json
uv run --locked python -m experiments.mqtt_clients --clients 1000 --output artifacts/mqtt-1000.json
```

The runner refuses more than 1,000 clients, remote hosts, alternate ports or more than 20 rounds. Clients connect sequentially at no more than 100 new clients/second, then execute short QoS 1 self-echo rounds. Each client uses a distinct socket and topic. A separate subscriber checks the broker's connected-client metric. That count includes the observer and may include a short-lived Docker health probe.

Paho uses socket callbacks with one asyncio event loop; no `loop_start()` or per-client network thread is used. TCP establishment itself is synchronous, limited to localhost and a two-second connection timeout. This feasibility choice is not a production asynchronous connector or reconnect scheduler. The sampled 512 MiB RSS threshold aborts a profile; it is not an operating-system memory quota. Queues and in-flight publications have explicit caps.

The replay tests disconnect a subscriber before manual PUBACK, create a new client object with the same MQTT identity and resume the broker session. They assert redelivery with the duplicate flag, then prove acknowledged messages do not replay on the next resume. This tests broker memory-backed session behavior, not persistence after a broker or host crash.

Outputs under `artifacts/` are ignored. Sanitized measurements from the completed run are under [evidence](evidence/mqtt-feasibility.md). The experiment is not part of the installed application wheel; run it from the repository with the dev dependency group installed.

## Source references

Implementation uses [Paho's socket/manual-ack APIs](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html), [Pydantic strict validation](https://docs.pydantic.dev/latest/concepts/strict_mode/), and [uv locked sync](https://docs.astral.sh/uv/concepts/projects/sync/). No infrastructure deployment beyond the disposable local test broker is part of Stage 3.
