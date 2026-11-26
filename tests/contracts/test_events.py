import json
from datetime import UTC, datetime, timedelta

import pytest

from medical_iot.contracts.events import validate_event


@pytest.fixture
def event():
    return {
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
        "data": {"uptime_seconds": 30, "charging": False},
    }


def parse(event, **kwargs):
    return validate_event(json.dumps(event).encode(), **kwargs)


@pytest.mark.parametrize(
    ("kind", "data"),
    [
        ("heartbeat", {"uptime_seconds": 0, "charging": True}),
        (
            "operational",
            {"state": "infusing", "rate_ml_per_hour": 1500, "volume_remaining_ml": 0.5},
        ),
        (
            "diagnostic",
            {"code": "OCCLUSION_SIMULATED", "severity": "critical", "message": "Synthetic"},
        ),
        (
            "firmware",
            {"previous_version": "2.4.0", "current_version": "2.4.1", "result": "success"},
        ),
    ],
)
def test_all_event_types_round_trip_without_losing_identity(event, kind, data):
    event.update(event_type=kind, data=data)
    result = parse(event)
    assert result.event_id == event["event_id"]
    assert result.model_dump(mode="json") == event


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("schema_version", "1"),
        ("schema_version", 2),
        ("battery_level", "87"),
        ("battery_level", 87.0),
        ("battery_level", True),
        ("battery_level", -1),
        ("battery_level", 101),
        ("sequence", 0),
        ("sequence", False),
        ("boot_sequence", 0),
        ("device_id", "PUMP-00000"),
        ("device_id", "PUMP-50001"),
        ("device_id", "PUMP-1"),
        ("device_id", "PUMP-00001\n"),
        ("timestamp", "2026-11-19T10:00:00+00:00"),
        ("timestamp", "2026-02-30T10:00:00Z"),
        ("timestamp", "2026-11-19 10:00:00Z"),
        ("timestamp", 123),
        ("event_id", "83C13913-CEC9-4C6A-B655-539E23092BCB"),
        ("boot_id", "bad-uuid"),
        ("firmware_version", "2.4"),
        ("firmware_version", "2.4.1-beta"),
        ("firmware_version", "123456789012345678901234567890.1.1"),
        ("connectivity", "unknown"),
        ("event_type", "commands"),
        ("data", None),
    ],
)
def test_invalid_envelope_is_rejected_without_coercion(event, field, value):
    event[field] = value
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize("field", ["device_id", "timestamp", "event_id", "sequence", "data"])
def test_required_fields_cannot_be_omitted(event, field):
    del event[field]
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize("nested", [False, True])
def test_unknown_fields_are_rejected(event, nested):
    (event["data"] if nested else event)["received_at"] = "client-forgery"
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize(
    "data",
    [
        {"uptime_seconds": -1, "charging": False},
        {"uptime_seconds": 0, "charging": "false"},
        {"uptime_seconds": True, "charging": False},
    ],
)
def test_heartbeat_data_is_strict(event, data):
    event["data"] = data
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize("rate", [True, "12.5", -0.1, 1500.1, float("nan"), float("inf")])
def test_operational_rate_rejects_invalid_or_nonfinite_numbers(event, rate):
    event.update(
        event_type="operational",
        data={
            "state": "idle",
            "rate_ml_per_hour": rate,
            "volume_remaining_ml": 1,
        },
    )
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize("volume", [-1, 3000.1, "1", True])
def test_operational_volume_limits(event, volume):
    event.update(
        event_type="operational",
        data={
            "state": "idle",
            "rate_ml_per_hour": 0,
            "volume_remaining_ml": volume,
        },
    )
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


def test_firmware_envelope_must_match_resulting_version(event):
    event.update(
        event_type="firmware",
        data={
            "previous_version": "2.4.0",
            "current_version": "2.4.2",
            "result": "success",
        },
    )
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        parse(event)


@pytest.mark.parametrize("device", ["PUMP-00001", "PUMP-50000"])
@pytest.mark.parametrize("battery", [0, 100])
def test_inclusive_device_and_battery_boundaries(event, device, battery):
    event.update(device_id=device, battery_level=battery)
    assert parse(event).device_id == device


def test_topic_identity_is_independent_of_payload_claim(event):
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        parse(event, expected_device_id="PUMP-00002")


@pytest.mark.parametrize(("delta", "code"), [(31, "CLOCK_INVALID"), (-86401, "EVENT_TOO_OLD")])
def test_clock_policy_is_deterministic(event, delta, code):
    now = datetime(2026, 11, 19, 10, tzinfo=UTC)
    event["timestamp"] = (now + timedelta(seconds=delta)).isoformat().replace("+00:00", "Z")
    with pytest.raises(ValueError, match=code):
        parse(event, received_at=now)


@pytest.mark.parametrize("delta", [30, -86400])
def test_clock_window_includes_exact_boundaries(event, delta):
    now = datetime(2026, 11, 19, 10, tzinfo=UTC)
    event["timestamp"] = (now + timedelta(seconds=delta)).isoformat().replace("+00:00", "Z")
    assert parse(event, received_at=now).device_id == "PUMP-00001"


@pytest.mark.parametrize(
    "payload", [b"{", b"[]", b"null", b"\xff", b'{"schema_version":1,"schema_version":1}']
)
def test_wire_boundary_rejects_ambiguous_or_invalid_json(payload):
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        validate_event(payload)


def test_wire_limit_is_bytes_not_characters(event):
    payload = json.dumps(event) + " " * 8192
    with pytest.raises(ValueError, match="PAYLOAD_TOO_LARGE"):
        validate_event(payload)
