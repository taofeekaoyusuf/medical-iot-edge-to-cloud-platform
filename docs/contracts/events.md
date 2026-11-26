# MQTT and event contracts — proposed version 1

Stage 3 implements the four telemetry event types in `src/medical_iot/contracts/events.py`. Status and receipt contracts remain documentation for later stages; no standalone JSON Schema files are published. See [development](../development.md) for validation entry points and limits.

## Transport topics and permissions

Use MQTT 5, QoS 1, UTF-8 JSON, TLS and a maximum application payload of 8 KiB. Telemetry events are not retained. Client IDs are unique per device. Configure persistent sessions with a proposed 10-minute expiry and keepalive of 30 seconds; reconnect with full jitter and an exponential delay capped at 60 seconds.

| Topic | Publisher | Subscriber | Meaning |
|---|---|---|---|
| `medical/v1/devices/{device_id}/events` | That device only | Gateway | Heartbeat, diagnostic, operational or firmware event |
| `medical/v1/devices/{device_id}/status` | That device or its broker-issued will | Gateway | Retained connection hint |
| `medical/v1/devices/{device_id}/receipts` | Authorized platform relay | That device only | Database commit receipt or permanent rejection |

Devices cannot publish receipt messages, subscribe to another device, or publish to another device's namespace. Service credentials use separate ACLs. Payload device ID must equal the ID in the authorized topic. MQTT subscribers do not receive the publisher's TLS certificate: the gateway relies on broker-enforced topic identity and adds its own trusted metadata. Payload claims never establish identity.

## Event envelope

All listed fields are required for all four event types; `data` varies by type. Unknown top-level fields are rejected in v1. Types have no implicit string/number coercion.

| Field | Type and constraint | Purpose |
|---|---|---|
| `schema_version` | Integer, exactly 1 | Contract selection |
| `event_id` | Canonical UUID string | Stable identity across retries |
| `device_id` | `PUMP-` plus exactly five decimal digits, 00001–50000 | Provisioned simulated identity |
| `timestamp` | UTC RFC3339 string ending in Z | Device generation time |
| `event_type` | `heartbeat`, `operational`, `diagnostic`, `firmware` | Payload discriminator |
| `boot_id` | UUID string | Unambiguous boot/session identity |
| `boot_sequence` | Integer >= 1, monotonically persisted per device | Orders restarts |
| `sequence` | Integer >= 1, increasing within a boot | Orders events within a boot |
| `battery_level` | Integer 0–100 | Simulated battery percentage |
| `firmware_version` | Three numeric components, maximum 32 characters | Simulator version report |
| `connectivity` | `online` or `offline` | Device-reported state, not authoritative health |
| `data` | Type-specific object below | Synthetic details |

```json
{
  "schema_version": 1,
  "event_id": "83c13913-cec9-4c6a-b655-539e23092bcb",
  "device_id": "PUMP-00001",
  "timestamp": "2026-11-19T10:00:00Z",
  "event_type": "heartbeat",
  "boot_id": "d04c2a63-7ad9-466e-8426-cf07587eefc9",
  "boot_sequence": 1,
  "sequence": 1,
  "battery_level": 87,
  "firmware_version": "2.4.1",
  "connectivity": "online",
  "data": {"uptime_seconds": 30, "charging": false}
}
```

| Event type | Required `data` fields; unknown fields rejected |
|---|---|
| heartbeat | `uptime_seconds`: integer >= 0; `charging`: boolean |
| operational | `state`: idle/infusing/paused/alarm; `rate_ml_per_hour`: finite number 0–1500; `volume_remaining_ml`: finite number 0–3000 |
| diagnostic | `code`: one of BATTERY_LOW, OCCLUSION_SIMULATED, SENSOR_TEST_FAILED, SELF_TEST_OK; `severity`: info/warning/critical; `message`: string <= 256 characters |
| firmware | `previous_version` and `current_version`: same version format; `result`: success/failed; current version equals envelope firmware version |

Ranges are synthetic scenario parameters, not clinical operating recommendations. `connectivity=offline` may appear in a replayed event; live health uses validated recent observations. Future clock values more than 30 seconds ahead are quarantined. Events older than the 24-hour replay window are permanently rejected, with a visible reason.

The simulator persists boot_sequence. Reprovisioning after losing that counter requires an explicit registry reset procedure; a reused boot_sequence with a different boot_id is quarantined. Sequence gaps are counted, not automatically treated as loss, until the replay/drain window closes. Reusing a sequence with different event content is a conflict.

## Status hint

A retained status object contains only `schema_version`, `device_id`, `boot_id`, `boot_sequence`, `connection_id` (UUID), `state` (online/offline), and `connected_at` (UTC). The will uses the same connection_id and an offline state. Its timestamp does not claim to be the disconnect time; the gateway records when it observes the will.

Status is a separate contract from the four event types. The Gateway sends a validated status observation with trusted ingress metadata to `status:v1`; a dedicated Health consumer handles it without inserting it into telemetry.events or issuing an application receipt. Repeated observations are idempotent by device/boot/connection/state.

A new online status establishes a connection_id for the boot. Older wills cannot replace a newer connection. Status is advisory: delayed retained messages and replay cannot prove liveness. Heartbeat expiry is the authoritative fallback; repeated status delivery has no duplicate notification effect.

## Trusted ingress metadata

The gateway adds `received_at`, `broker_shard`, `topic`, `authenticated_device_id` (derived from the ACL-protected topic), and `ingress_id`. Client input cannot set these fields. Replay can produce multiple ingress observations for one immutable event. Validate active registration again before durable processing if the registry state changes during buffering.

## Application receipts

An MQTT PUBACK only confirms that MQTT hop. The simulator retains events in its disk spool until a platform receipt, not just PUBACK. Proposed commit receipt:

```json
{
  "schema_version": 1,
  "device_id": "PUMP-00001",
  "event_id": "83c13913-cec9-4c6a-b655-539e23092bcb",
  "result": "committed",
  "committed_at": "2026-11-19T10:00:01Z"
}
```

Receipts use the restricted receipt topic, QoS 1, and are not retained. Duplicates produce another receipt referencing the original commit time. A receipt must match a pending event/device before removing it from the spool. No receipt within 60 seconds triggers paced replay with the original event ID. Limit retries by the 24-hour replay window and bounded spool policy; expired/overflowed events remain explicit loss counters.

A permanent rejection receipt adds `reason_code` from SCHEMA_INVALID, EVENT_TOO_OLD, IDENTITY_MISMATCH, DEVICE_DISABLED, EVENT_CONFLICT or CLOCK_INVALID and omits committed_at. It is sent only when the device/event identifiers are safely validated; unidentifiable malformed data goes to a bounded quarantine without a receipt. Transient outages do not produce permanent rejection receipts.

[The Paho client API](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html) exposes manual acknowledgement for incoming messages. Gateway implementation must test this path and defer its subscription ACK until enqueue succeeds. This still does not make broker or Redis memory durable; the application receipt closes that gap within the spool/replay limits.
