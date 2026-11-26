# ADR-0002: Commit receipts and idempotent database effects

Status: Proposed for implementation review.

## Context

QoS 1 can redeliver, broker acknowledgement is not a PostgreSQL commit, and a successful Redis append may precede durable disk synchronization. Worker and host failures cross several acknowledgement boundaries.

## Decision

Retain source events in a bounded disk spool until an application commit receipt. Preserve event IDs on retry. Atomically store telemetry, uniqueness records and outbox messages in PostgreSQL. Acknowledge stream work only after commit. Regenerate receipts on duplicate ingestion. Use a distinct unpartitioned uniqueness ledger if raw history is partitioned. Downstream services store processed-event markers with state changes.

## Alternatives

MQTT QoS 2 alone does not transact the database. A volatile deduplication cache cannot enforce persistence-level uniqueness. Synchronously writing the database in the gateway couples ingestion to database outages. A durable replicated log could strengthen the transport boundary but still requires idempotent consumers and verified failure semantics.

## Consequences

Receipts and outboxes add storage, network and operational overhead. Delivery is limited by replay age, source-spool survival and bounded capacity. Post-receipt database disaster recovery depends on backups. Redis can be replaced through a future adapter only if the same acceptance tests hold. See [delivery design](../data-and-delivery.md).
