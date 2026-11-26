# ADR-0003: Per-device TLS identity and explicit broker sharding

Status: Proposed for implementation review.

## Context

Thousands of synthetic devices must be independently identifiable. Service replication and broker-session replication are different problems. Shared credentials would weaken the connection demonstration.

## Decision

Require a per-device client certificate and ACL-protected topics. Bind payload device identity to the topic. Use broker-enforced identity rather than trusting client JSON. Keep one Mosquitto shard initially; scale experiments use an explicit assignment manifest and persistent volume per shard. Gateway workers may use verified shared-subscription behavior, while device commit receipts provide replay across failures.

## Alternatives

A fleet-wide password is easy but cannot demonstrate per-device isolation. Stateless load balancing over independent brokers hides session ownership and recovery gaps. A replicated MQTT product or cloud ingress may meet stronger HA goals, but needs a separate selection, cost and fault-test decision.

## Consequences

Certificate enrollment, revocation and connection termination need explicit lifecycle tests. Shard outage affects its assigned devices. Client reconnects and replay restore delivery within source limits, not broker-level replicated state. No cross-zone HA claim is made for the Mosquitto design. See [security](../security.md) and [cloud options](../architecture/cloud.md).
