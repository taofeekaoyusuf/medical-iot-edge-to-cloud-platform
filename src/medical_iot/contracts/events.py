"""Strict version-1 wire validation; persistence and ordering require later stages."""

import json
import re
from datetime import datetime, timedelta
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

MAX_PAYLOAD_BYTES = 8192


def canonical_uuid(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("UUID must use canonical lowercase hyphenated form")
    return value


def utc_timestamp(value: str) -> str:
    if not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", value
    ):
        raise ValueError("Expected UTC RFC3339 ending in Z")
    datetime.fromisoformat(value)  # Reject impossible calendar dates and clock values.
    return value


def device_identity(value: str) -> str:
    if not re.fullmatch(r"PUMP-[0-9]{5}", value) or not 1 <= int(value[5:]) <= 50000:
        raise ValueError("Expected device PUMP-00001 through PUMP-50000")
    return value


UuidString = Annotated[str, AfterValidator(canonical_uuid)]
UtcTimestamp = Annotated[str, AfterValidator(utc_timestamp)]
DeviceId = Annotated[str, AfterValidator(device_identity)]
FirmwareVersion = Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$", max_length=32)]
PositiveInteger = Annotated[int, Field(ge=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class HeartbeatData(StrictModel):
    uptime_seconds: Annotated[int, Field(ge=0)]
    charging: bool


class OperationalData(StrictModel):
    state: Literal["idle", "infusing", "paused", "alarm"]
    rate_ml_per_hour: Annotated[float, Field(ge=0, le=1500)]
    volume_remaining_ml: Annotated[float, Field(ge=0, le=3000)]


class DiagnosticData(StrictModel):
    code: Literal["BATTERY_LOW", "OCCLUSION_SIMULATED", "SENSOR_TEST_FAILED", "SELF_TEST_OK"]
    severity: Literal["info", "warning", "critical"]
    message: Annotated[str, Field(max_length=256)]


class FirmwareData(StrictModel):
    previous_version: FirmwareVersion
    current_version: FirmwareVersion
    result: Literal["success", "failed"]


class Envelope(StrictModel):
    # An int constraint rejects bool, unlike Literal[1] alone in some validators.
    schema_version: Annotated[int, Field(ge=1, le=1)]
    event_id: UuidString
    device_id: DeviceId
    timestamp: UtcTimestamp
    boot_id: UuidString
    boot_sequence: PositiveInteger
    sequence: PositiveInteger
    battery_level: Annotated[int, Field(ge=0, le=100)]
    firmware_version: FirmwareVersion
    connectivity: Literal["online", "offline"]


class Heartbeat(Envelope):
    event_type: Literal["heartbeat"]
    data: HeartbeatData


class Operational(Envelope):
    event_type: Literal["operational"]
    data: OperationalData


class Diagnostic(Envelope):
    event_type: Literal["diagnostic"]
    data: DiagnosticData


class Firmware(Envelope):
    event_type: Literal["firmware"]
    data: FirmwareData

    @model_validator(mode="after")
    def consistent_version(self) -> Self:
        if self.data.current_version != self.firmware_version:
            raise ValueError("Resulting firmware must match the envelope")
        return self


Event = Annotated[
    Heartbeat | Operational | Diagnostic | Firmware, Field(discriminator="event_type")
]
EVENT_ADAPTER = TypeAdapter(Event)


class EventValidationError(ValueError):
    """Stable reason codes without echoing untrusted payloads into logs."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("Nonfinite JSON number")


def validate_event(
    payload: bytes | str,
    *,
    expected_device_id: str | None = None,
    received_at: datetime | None = None,
) -> Event:
    """Validate wire content; optionally apply trusted topic identity and ingress-time policy.

    Clock policy is explicit so offline schema validation never depends on wall time.
    The caller must supply trusted metadata, not values extracted from device JSON.
    """
    try:
        wire = payload.encode("utf-8") if isinstance(payload, str) else payload
        if not isinstance(wire, bytes):
            raise ValueError("Expected UTF-8 bytes or text")
        if len(wire) > MAX_PAYLOAD_BYTES:
            raise EventValidationError("PAYLOAD_TOO_LARGE")
        raw = json.loads(
            wire.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_constant
        )
        event = EVENT_ADAPTER.validate_python(raw)
    except EventValidationError:
        raise
    except (ValueError, UnicodeError, RecursionError, ValidationError) as exc:
        raise EventValidationError("SCHEMA_INVALID") from exc
    if expected_device_id is not None and event.device_id != expected_device_id:
        raise EventValidationError("IDENTITY_MISMATCH")
    if received_at is not None:
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")
        age = received_at - datetime.fromisoformat(event.timestamp)
        if age < timedelta(seconds=-30):
            raise EventValidationError("CLOCK_INVALID")
        if age > timedelta(hours=24):
            raise EventValidationError("EVENT_TOO_OLD")
    return event
