# Data ownership, buffering and delivery

Status: proposed design. The guarantee is at-least-once attempts with idempotent database effects inside a finite replay window. There is no claim of unlimited losslessness or end-to-end exactly-once delivery.

## Logical data model

| Schema / tables | Owner | Key invariant |
|---|---|---|
| registry.devices, credentials, operations, audit | Registry | Unique device ID; no private keys; explicit provisioning state |
| telemetry.event_keys | Processor | Primary key (device_id,event_id); content digest and original commit time |
| telemetry.events | Processor | Immutable payload plus trusted ingress metadata |
| telemetry.boots | Processor | One boot_id per device/boot_sequence |
| telemetry.sequences | Processor | Unique device/boot_sequence/sequence maps to one event digest |
| telemetry.outbox | Processor | Domain event and commit receipt created with database commit |
| health.device_state, processed_events, outbox | Health | Monotonic state version; idempotent transition processing |
| notifications.incidents, processed_events, audit | Notification | One open incident per device/rule; no duplicate creation |
| api.idempotency | API | Actor/route/key uniquely identifies request and response |

PostgreSQL is authoritative. Use bounded connection pools; initial proposal is at most 5 connections per service replica, explicitly budgeted against server capacity before scaling.

Raw events may be partitioned by trusted received date after measurement. PostgreSQL partitioned uniqueness depends on partition keys, so a separate unpartitioned event_keys ledger enforces device/event uniqueness across partitions. See [PostgreSQL partitioning constraints](https://www.postgresql.org/docs/current/ddl-partitioning.html). Do not create a daily-partition-only uniqueness constraint and call it global deduplication.

## Commit path

1. The simulator writes an event to its bounded local disk spool before publishing.
2. Mosquitto verifies identity and topic permissions. A publisher PUBACK is not a database receipt.
3. The Gateway validates the event and appends it to `ingress:v1` in Redis. It acknowledges its MQTT subscription delivery only after successful append. On Redis failure, limit in-flight work and disconnect/back off rather than accumulate unbounded memory.
4. Processor consumers in group `telemetry-v1` validate again and open a PostgreSQL transaction. Insert the deduplication key, sequence mapping, raw event, and outbox entries atomically. A same-key/same-content replay has no repeated state effect and schedules a fresh receipt; same-key/different-content is quarantined as a conflict.
5. Commit PostgreSQL, then acknowledge the Redis entry. If the worker dies between these steps, replay follows the duplicate path.
6. The outbox relay publishes domain events to `domain:v1` and receipts to MQTT, then marks outbox delivery. A crash after publication produces duplicate delivery, handled by downstream keys. Use bounded batches and row leases/locking so multiple relays do not contend indefinitely.
7. Health consumes domain events in its own group; notifications consume health transitions in another group. Each consumer commits its own processed-event marker and state change in one transaction before stream acknowledgement.
8. Receipt arrival removes the matching simulator spool item. Lost receipts cause replay and regeneration of the receipt, even if the first outbox row was already marked sent.

This receipt mechanism is a project design, not a feature supplied automatically by MQTT. It adds bandwidth, disk and transaction cost that benchmarks must include.

## Redis durability and queue limits

Ingress events use `ingress:v1`; domain events use `domain:v1`; advisory connectivity observations use `status:v1` with only the Health consumer group. Each stream has independent capacity and acknowledgement watermarks. Device event receipt regeneration applies to telemetry events, not status hints.

Use AOF persistence and a persistent volume. The initial `everysec` profile permits a short recent-write loss window during host failure; it is not synchronous durable acknowledgement. Test `always` separately if needed, with throughput impact recorded. See [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/).

Proposed source-spool defaults are 10,000 events or 64 MiB per worker, whichever arrives first, with at most 24 hours replay age. Cap each worker at a declared device range; record the combined budget when adding workers. At the limit, pause synthetic generation and count skipped scheduled samples, while retaining already-spooled uncommitted events; never silently evict them. Expired items are moved to a bounded summary ledger with explicit expiry counters. The replay scheduler reserves capacity for live heartbeats so reconnect backlog cannot indefinitely suppress fresh liveness observations.

The simulator spool and commit receipts recover Redis/broker loss only while the original source spool survives and entries remain inside its limits. Host/disk loss that destroys both local source and backend is outside that guarantee. A committed database failure after a receipt requires database restore; source replay is not a substitute for backups.

Initial demo limits: 100,000 entries or 256 MiB estimated payload per stream, whichever arrives first; Redis maxmemory 384 MiB under a 512 MiB container ceiling with `noeviction`. Actual memory overhead may trigger backpressure sooner. Track byte estimates plus Redis memory, not just entry counts. Full queues reject new admission; never use blind MAXLEN trimming to delete pending work.

A retention job computes a safe watermark across every relevant consumer group's delivered and pending entries, deleting only fully processed entries. Reclaim stale pending work after a 60-second lease with bounded `XAUTOCLAIM` batches and a worker heartbeat; long jobs renew ownership rather than being immediately duplicated. The [Redis Streams documentation](https://redis.io/docs/latest/develop/data-types/streams/) describes consumer groups and reclaiming.

After five failed processing attempts, persist a bounded dead-letter record with reason, event identity and digest before acknowledging. If dead-letter persistence is unavailable, retain pending work. A manual replay preserves event IDs and records operator/replay audit data. Malformed payload samples are capped at 1 KiB and sensitive fields must be excluded.

## Retention and ordering

Proposed demo defaults: raw telemetry 24 hours; deduplication keys, sequence mappings and delivered outbox rows 48 hours; incidents/audit 7 days; metrics 24 hours. Undelivered outbox records are not expired. Devices allow replay only up to 24 hours. These values are experiment controls, not suitable production retention guarantees. Enforce disk budgets (initial 5 GiB raw telemetry budget) and stop admission with visible alerts before storage exhaustion; a full-rate 50,000-device run cannot keep a day's data within that demo budget.

Latest state uses the ordered pair (boot_sequence,sequence), never arrival order alone. Events with older order are kept as history but cannot roll state back. A heartbeat affects liveness only if its generation time is within 90 seconds of trusted ingress time and its ordering is current. Fleet health includes observation age, so queue delays remain visible.

Notification rules: low battery opens below 20% and resolves at >=25%; simulated critical diagnostics open by rule and resolve only through the documented matching recovery event. Acknowledgement records operator attention without clearing a fault. Offline opens after 90 seconds without a fresh heartbeat, with a 10-second sweeper interval; a recent valid heartbeat resolves it. Emit one transition per state_version, not one notification per input event.
