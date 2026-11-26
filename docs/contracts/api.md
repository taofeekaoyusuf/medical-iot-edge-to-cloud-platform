# Application and registry API contracts

Status: proposed `/v1` REST API. OpenAPI and executable validators are deferred to implementation. JSON requests/responses use UTC RFC3339 timestamps. No pump-control endpoint is planned.

## Authorization

Validate signature using trusted issuer keys, algorithm allowlist, issuer, audience, expiry and not-before. Use separate service credentials for internal APIs. A local OIDC provider is the initial user-token issuer; cloud OIDC changes configuration, not permission semantics.

| Role | Allowed operations |
|---|---|
| viewer | Read devices, telemetry, health, fleet summaries and notifications |
| operator | Viewer actions plus notification acknowledgement |
| administrator | Operator actions plus device provisioning, disable and credential rotation |

This is initially a single synthetic fleet. Do not claim tenant isolation. Device client certificates cannot authenticate to application administration APIs.

## Routes

| Method and path | Minimum role | Response / semantics |
|---|---|---|
| GET `/v1/devices` | viewer | 200, cursor page; filter health, connectivity and firmware |
| GET `/v1/devices/{id}` | viewer | 200 identity plus latest state, or 404 |
| GET `/v1/devices/{id}/telemetry` | viewer | 200 time-bounded cursor page, optionally filtered by event_type |
| GET `/v1/devices/{id}/health` | viewer | 200 component states and observation timestamps |
| GET `/v1/fleet/summary` | viewer | 200 counts and explicit `as_of` timestamp |
| GET `/v1/notifications` | viewer | 200 cursor page; filters device, severity and state |
| POST `/v1/notifications/{id}/acknowledgements` | operator | 200 acknowledged incident, audited actor/time |
| POST `/v1/devices` | administrator | 202 pending registration; registry reconciles broker permissions |
| POST `/v1/devices/{id}/disable` | administrator | 202 disabling; terminal disabled only after reconciliation |
| POST `/v1/devices/{id}/credentials/rotate` | administrator | 202 pending rotation; CSR-based, no private key returned |
| GET `/v1/operations/{operation_id}` | relevant actor or administrator | 200 pending/succeeded/failed plus sanitized reason |
| GET `/health/live` | local/internal | 200 process functioning; no dependency details |
| GET `/health/ready` | local/internal | 200 ready or 503 unavailable |

Health/metrics endpoints are not public application routes. GET telemetry requires `from` and `to`; maximum interval 24 hours, default last hour. Pagination uses limit 1–200 (default 50), opaque cursors and stable ordering by received_at plus event_id. Invalid/expired cursors return 400. Counts may lag ingestion and must report freshness.

Example device response shape: `device_id`, `registration_status`, `firmware_version`, `battery_level`, `connectivity_state`, `health_state`, `last_observed_at`, `state_version`, `as_of`. Never return private keys or bearer credentials.

## Mutations and errors

Registration accepts a device ID and optional descriptive label (<= 80 characters). Credential rotation accepts a PEM CSR up to 16 KiB and validates its requested identity; a trusted administrative provisioning flow creates and distributes credentials. Disabling accepts a reason <= 256 characters. Notification acknowledgement accepts an optional comment <= 256 characters; it does not resolve the underlying condition.

Mutating routes require an `Idempotency-Key` UUID. Store a request hash and result for 24 hours, scoped to actor and route. Identical retry returns the same operation; a changed request under the same key returns 409. A duplicate registered device ID also returns 409. Clients poll asynchronous operations until terminal state. Audit records include actor, action, target and outcome.

Errors use `code`, `message`, `request_id`, and optional field-level `details`. Use 400 for malformed parameters, 401 for absent/invalid identity, 403 for insufficient permission, 404 for unknown resources, 409 for conflicts, 413 for excessive size, 422 for field validation, 429 with Retry-After for rate limits, and 503 for temporary dependency unavailability. Do not expose stack traces or secrets.

Public API Service forwards writes to the Registry or Notification Service over authenticated internal APIs. Gateway reads an internal registry snapshot using its own least-privilege identity. A proposed registry cache TTL of 30 seconds bounds stale decisions; on cache expiry with the registry unavailable, new event validation fails closed and clients retain/replay events. Disabling must reconcile both the broker connection and registry state; it is not complete merely because an HTTP request was accepted.
