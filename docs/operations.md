# Operations, observability and recovery

Status: intended operating behavior and future runbook requirements. No platform commands exist yet.

## Metrics and dashboards

Prometheus scrapes services and scoped infrastructure exporters; Grafana presents fleet, ingestion, processing, storage and recovery dashboards. Proposed metrics include:

| Metric | Meaning |
|---|---|
| simulator_active_connections | Actual connected MQTT clients, distinct from configured identities |
| simulator_events_generated_total / committed_total / rejected_total / expired_total | End-to-end accounting |
| gateway_events_total by outcome | Accepted, malformed, disabled, oversized or backpressured |
| processor_events_total by outcome | Committed, duplicate, conflict or dead-lettered |
| processing_latency_seconds | Trusted ingress-to-database-commit duration histogram |
| stream_pending_entries / oldest_pending_age_seconds | Backlog and recovery pressure |
| reconnect_attempts_total | Connection churn and storm intensity |
| outbox_oldest_unsent_age_seconds | Delay between database commit and downstream delivery |
| fleet_devices by health | Aggregate status, without one series per device |

Use bounded labels such as service, outcome and broker shard. Never label Prometheus series with device ID, event ID or certificate fingerprint. Put these in sampled structured logs or database queries. This follows [Prometheus label guidance](https://prometheus.io/docs/practices/naming/).

Structured logs include service, level, timestamp, request/ingress ID, event ID when relevant, and reason code. Rotate logs and cap retained size. Prometheus is metrics storage, not a log store; optional local Loki integration is a later decision if Docker memory permits. Start with searchable service/container logs.

Alert proposals: processing p95 >5 seconds for 2 minutes; oldest ingress >30 seconds for 1 minute; queue or spool >80% capacity; database volume >80%; certificate expiry <7 days; sustained reconnects; no telemetry commits despite active generation. Track recovery separately from steady-state latency.

## Horizontal scaling

Benchmark processor replicas 1, 2 and 4 with the same input and shared database capacity. API/gateway pods may scale on CPU; processors should eventually scale on pending age/lag via a metric adapter or KEDA, with one controller per deployment. Set min/max replicas, cooldown and connection-pool budgets. CPU-based HPA requires metrics availability and correctly configured resource requests; [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) describes the mechanism.

Registry reconciliation and health expiry sweeps use leases or advisory locks. Domain processing uses transactional state guards and unique keys so multiple workers cannot produce repeated transitions. Shutdown stops new work, drains bounded in-flight operations, and leaves uncommitted entries for reclaim.

A source IP cannot necessarily sustain 50,000 connections to a single destination because ephemeral ports, TIME_WAIT and NAT mappings are finite. Measure file-descriptor limits, TLS memory, reconnect churn and Docker NAT behavior. Split clients across broker endpoints or independent source addresses only when genuinely provisioned; extra containers alone do not prove independent egress addresses.

## Failure matrix

| Fault injection | Expected response | Evidence |
|---|---|---|
| Kill processor before DB commit | Redis pending entry reclaimed; no partial transaction | Pending age and eventual unique event row |
| Kill processor after commit before XACK | Replay deduplicated; commit receipt regenerated | One immutable event and bounded duplicate counter |
| Restart gateway | Broker retry and/or device replay | Matching event-ID accounting after drain |
| Restart broker shard | Jittered reconnect and replay from source spool | Recovery time, successful connection count, no claim of cross-shard replication |
| Stop Redis for 60 seconds | Ingress backpressure, bounded memory, no false commit receipt | Spool growth then drain; queue/heap plots |
| Stop PostgreSQL for 60 seconds | No acknowledgement of uncommitted work; retries bounded | Backlog grows, no commit receipts until commit resumes |
| Lose receipt delivery | Simulator replays; duplicate generates another receipt | Spool eventually clears without duplicate DB effect |
| Fill a queue/spool/disk budget | Visible rejection/expiry or paused admission per policy | No silent deletion and no out-of-memory crash |
| Expire/revoke certificate | New connection denied; active session enforcement tested | Broker rejection and registry terminal operation |
| Delete a disposable database volume | Restore explicitly selected backup into isolated instance | Verified row counts and documented RPO/RTO |

Database restore tests must never use the only copy of local data. Logical backups are suitable initial demo artifacts, encrypted/ignored outside Git; add WAL-based recovery only in its own approved task. Preserve registry, deduplication, health, notifications and outboxes consistently. Restore outbox jobs with duplicate-safe consumers. Record backup time and accepted transactions lost after that time.

Offline detection uses a 90-second heartbeat timeout and 10-second sweep. Under backlog, show ingestion freshness and a platform-degraded status alongside fleet connectivity so an ingestion outage is not misrepresented as simultaneous confirmed device failure.

## Evidence and cleanup

Every future run records commit, configuration, versions, seed, CPU/RAM limits, connection count, unique events, duplicates, pending/expired work, latency distribution and duration. Compare generated identities to terminal and pending outcomes after a defined drain period. Retain a short machine-readable summary and sanitized logs; do not commit bulk telemetry.

Stopping the stack should preserve volumes by default. Destructive cleanup, backup deletion, credential replacement and resource-limit increases need explicit scope in the approved run. Cloud cleanup has a separate gate in the cloud design.
