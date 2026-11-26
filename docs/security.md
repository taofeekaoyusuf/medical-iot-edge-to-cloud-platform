# Security and identity design

Status: proposed controls for synthetic demonstrations, not medical-device certification or a compliance claim.

## Device enrollment and certificate lifecycle

An administrator registers an identity; it remains pending until credentials and broker permissions are provisioned. Generate per-device private keys locally, create CSRs, and use a development CA whose private key stays outside Git and container images. Issue certificate identities that map exactly to the permitted device topic. Verify broker hostname/SAN and trust chain in clients. Do not disable server verification for convenience.

Mosquitto will require client certificates and derive the ACL identity from the certificate CN using `use_identity_as_username`. Device CNs are strictly validated against the device-ID format. The gateway cannot authenticate the original publisher from arbitrary payload fields. See [Mosquitto TLS configuration](https://mosquitto.org/man/mosquitto-conf-5.html).

Proposed certificate lifetimes are 30 days for demo devices and 90 days for the broker, with expiry alerts at seven days. These are project policy proposals. Rotation permits a bounded overlap of at most 24 hours between old and new credentials. Broker certificate hot reload support and reconnect behavior must be tested for the pinned version before claiming no downtime.

Revocation removes publish/subscribe permissions, updates the certificate revocation mechanism, and disconnects existing sessions. A CRL update alone does not prove that an existing TLS connection has stopped. The initial fallback is a controlled restart of the affected local shard, followed by reconnect/replay. Registry operations remain disabling/rotating until enforcement is verified. Gateway registry checks provide a second control during reconciliation.

## Service and application identities

Assign separate service certificates/credentials, Redis ACLs and PostgreSQL roles. Allow the processor to write telemetry but not registration; allow the API only approved read views and owner-service calls. Restrict metric exporters to required reads. Place internal APIs and data stores on private container networks.

Application JWT validation and role rules are defined in [API contracts](contracts/api.md). Fail closed on invalid issuer/audience/signature, expired token, unknown signing key or missing permission. Key rollover uses a bounded refresh path; an unrecognized key does not bypass validation.

## Secrets and abuse controls

Store local secrets in ignored files mounted read-only with restrictive host permissions. Kubernetes Secret objects still require encryption-at-rest and RBAC planning; base64 encoding is not protection. Cloud secret management is documented separately and not implemented.

Bound payload sizes, connections, in-flight messages, queues and API request rates. Registration and certificate endpoints require administrator permissions and audit records. Log rejection codes without private keys, tokens, full certificates or unnecessary payloads. Public repository examples use only synthetic data.

Supply-chain work in later stages will pin dependencies and images, run as non-root where supported, minimize capabilities and filesystem writes, and scan artifacts before publishing. Security tests must include invalid/expired certificates, cross-device topic access, forged receipts, disabled devices, token role failures, malformed JSON and oversized messages.
