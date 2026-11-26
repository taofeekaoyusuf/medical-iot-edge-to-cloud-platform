# Implementation checklist

Stage 2 is documentation only. All implementation tasks below are pending and require their stage approval. Paths are proposed, not existing files. Split a task further before execution if it grows beyond roughly five files.

## Stage 2 documentation review

- [x] Verify local Markdown links and JSON examples.
- [x] Check requirement coverage and acknowledgement/failure consistency.
- [x] Check staged changes contain documentation only.

## T01: Reproducible Python foundation

- [ ] Implement after permission.

**Reason:** Provide a locked environment and consistent checks before services diverge.

**Tools:** uv, Python, Ruff, pytest. **Dependencies:** None. **Scope:** 1–4 proposed files.

**Likely files:** pyproject.toml; uv.lock; tests/conftest.py.

**Acceptance:** Environment sync is repeatable; lint and a minimal meaningful configuration test pass.

**Verification:** Create a clean environment and run the documented checks.

## T02: Shared event validation

- [ ] Implement after permission.

**Reason:** Make one contract authoritative across producers and consumers.

**Tools:** Pydantic, pytest. **Dependencies:** T01. **Scope:** 1–4 proposed files.

**Likely files:** packages/contracts/events.py; tests/contracts/test_events.py.

**Acceptance:** All four event types and invalid boundary examples behave as specified.

**Verification:** Run event-contract tests including unknown fields and non-finite numeric values.

## T03: MQTT feasibility spike

- [ ] Implement after permission.

**Reason:** Verify external-loop clients and deferred ACK before adopting a high-scale client.

**Tools:** Paho candidate, MQTT test harness. **Dependencies:** T01. **Scope:** 1–4 proposed files.

**Likely files:** experiments/mqtt_clients.py; tests/integration/test_mqtt_ack.py; docs/evidence/mqtt-feasibility.md; tests/compose.yaml.

**Acceptance:** No thread per device; delayed ACK and reconnect replay are observed; resource curves recorded.

**Verification:** Run small and stepped connection experiments under an explicit cap.

**Checkpoint after T03:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T04: Device registration slice

- [ ] Implement after permission.

**Reason:** Persist identities and provisioning operations with explicit lifecycle states.

**Tools:** FastAPI, PostgreSQL, Alembic. **Dependencies:** T01. **Scope:** 1–4 proposed files.

**Likely files:** services/registry/app.py; services/registry/models.py; migrations/registry.py; tests/integration/test_registration.py.

**Acceptance:** Duplicate registration is rejected; operation state survives restart.

**Verification:** Test registration retries and database restart.

## T05: Certificate and ACL lifecycle

- [ ] Implement after permission.

**Reason:** Bind every device to its topics and demonstrate disable behavior.

**Tools:** Local CA tooling, Mosquitto TLS/ACLs. **Dependencies:** T03, T04. **Scope:** 1–4 proposed files.

**Likely files:** tools/provision_devices.py; infrastructure/mosquitto/config; services/registry/reconcile.py; tests/integration/test_device_auth.py.

**Acceptance:** Per-device certificates work; cross-device access fails; revoked active sessions are disconnected.

**Verification:** Exercise enrollment, rotation overlap, revocation and reconnect denial.

**Checkpoint after T05:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T06: Deterministic simulator

- [ ] Implement after permission.

**Reason:** Generate reproducible synthetic states and independently report identities/connections.

**Tools:** Python async client, seeded scenarios. **Dependencies:** T02, T03, T05. **Scope:** 1–4 proposed files.

**Likely files:** simulator/devices.py; simulator/runner.py; simulator/scenarios.py; tests/unit/test_simulator.py.

**Acceptance:** Unique ranges; paced event mix; identical seed reproduces generation.

**Verification:** Compare deterministic event manifests and actual connected-client counts.

## T07: Source spool and replay

- [ ] Implement after permission.

**Reason:** Retain uncommitted events across process restart with bounded resource use.

**Tools:** Local disk spool, Python. **Dependencies:** T06. **Scope:** 1–4 proposed files.

**Likely files:** simulator/spool.py; simulator/replay.py; tests/integration/test_spool.py.

**Acceptance:** Receipt removes only matching event; original IDs survive restart; overflow/expiry counted.

**Verification:** Crash the worker and replay; inject forged receipts and capacity limits.

**Checkpoint after T07:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T08: Gateway ingestion

- [ ] Implement after permission.

**Reason:** Validate authenticated topic identity and append bounded asynchronous work.

**Tools:** Paho manual ACK, Redis Streams. **Dependencies:** T02, T05, T07. **Scope:** 1–4 proposed files.

**Likely files:** services/gateway/app.py; services/gateway/validation.py; services/gateway/queue.py; tests/integration/test_gateway.py.

**Acceptance:** Malformed/disabled traffic rejected; ACK follows enqueue; Redis outage does not grow memory unbounded.

**Verification:** Fault-test enqueue before and after subscriber acknowledgement.

## T09: Idempotent telemetry persistence

- [ ] Implement after permission.

**Reason:** Make the first accepted event authoritative without duplicate database effects.

**Tools:** PostgreSQL transactions, Redis consumer groups. **Dependencies:** T08. **Scope:** 1–4 proposed files.

**Likely files:** services/processor/app.py; services/processor/store.py; migrations/telemetry.py; tests/integration/test_dedup.py.

**Acceptance:** Same event deduplicates; conflicts quarantine; ordering survives duplicate replay.

**Verification:** Kill worker before/after commit and verify uniqueness and pending reclaim.

## T10: Outbox and commit receipts

- [ ] Implement after permission.

**Reason:** Close the source-to-database acknowledgement boundary.

**Tools:** PostgreSQL outbox, MQTT relay. **Dependencies:** T09. **Scope:** 1–4 proposed files.

**Likely files:** services/processor/outbox.py; services/processor/receipts.py; tests/integration/test_receipts.py.

**Acceptance:** Committed event receives receipt; duplicate regenerates receipt; relay crash has no duplicate semantic effect.

**Verification:** Drop first receipt and crash relay after publication.

**Checkpoint after T10:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T11: Health transitions

- [ ] Implement after permission.

**Reason:** Derive current health without stale replay reversing state.

**Tools:** Python worker, PostgreSQL leases. **Dependencies:** T10. **Scope:** 1–4 proposed files.

**Likely files:** services/health/app.py; services/health/rules.py; migrations/health.py; tests/unit/test_health.py.

**Acceptance:** Offline timeout and battery hysteresis pass; old events/wills cannot overwrite current state.

**Verification:** Use controlled time and reordered input; test concurrent sweepers.

## T12: Operational incidents

- [ ] Implement after permission.

**Reason:** Persist, suppress, acknowledge and resolve operational notifications.

**Tools:** Python worker, PostgreSQL. **Dependencies:** T11. **Scope:** 1–4 proposed files.

**Likely files:** services/notifications/app.py; services/notifications/rules.py; migrations/notifications.py; tests/integration/test_incidents.py.

**Acceptance:** One open incident per rule/device; ACK is not resolution; duplicate transitions harmless.

**Verification:** Replay transitions and race duplicate consumers.

**Checkpoint after T12:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T13: Authorized read API

- [ ] Implement after permission.

**Reason:** Expose useful paginated device and fleet queries.

**Tools:** FastAPI, OIDC validation. **Dependencies:** T12. **Scope:** 1–4 proposed files.

**Likely files:** services/api/app.py; services/api/auth.py; services/api/queries.py; tests/integration/test_read_api.py.

**Acceptance:** Bounded time queries and stable cursors; invalid identity/role rejected.

**Verification:** Run endpoint/role matrix and pagination-under-ingestion tests.

## T14: Administrative API operations

- [ ] Implement after permission.

**Reason:** Route lifecycle changes to owners with idempotency and audit.

**Tools:** FastAPI, owner-service clients. **Dependencies:** T13. **Scope:** 1–4 proposed files.

**Likely files:** services/api/operations.py; services/api/idempotency.py; tests/integration/test_admin_api.py.

**Acceptance:** Retry returns original operation; changed payload conflicts; viewer mutations denied.

**Verification:** Test actor-scoped keys and operation completion/failure.

**Checkpoint after T14:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T15: Service metrics

- [ ] Implement after permission.

**Reason:** Measure latency, outcomes and recovery without excessive cardinality.

**Tools:** Prometheus client. **Dependencies:** T14. **Scope:** 1–4 proposed files.

**Likely files:** packages/observability/metrics.py; packages/observability/logging.py; tests/unit/test_metric_labels.py.

**Acceptance:** Bounded labels; secrets excluded; accounting distinguishes commit/reject/expiry.

**Verification:** Inspect scrape output and sample structured logs under faults.

## T16: Dashboards and alerts

- [ ] Implement after permission.

**Reason:** Expose health, resource pressure and backlog in one local view.

**Tools:** Grafana, Prometheus. **Dependencies:** T15. **Scope:** 1–4 proposed files.

**Likely files:** infrastructure/monitoring/prometheus.yml; infrastructure/monitoring/alerts.yml; infrastructure/monitoring/dashboard.json; docs/monitoring.md.

**Acceptance:** Dashboard panels populate; alerts fire and clear during controlled faults.

**Verification:** Validate provisioning and rule behavior against recorded scenarios.

## T17: Full Compose demonstration

- [ ] Implement after permission.

**Reason:** Provide a repeatable local stack with bounded resources.

**Tools:** Docker, Compose. **Dependencies:** T16. **Scope:** 1–4 proposed files.

**Likely files:** Dockerfile; compose.yaml; .env.example; docs/local-runbook.md.

**Acceptance:** Clean startup with persistent volumes; loopback exposure only; smoke path passes.

**Verification:** Run clean start, restart and non-destructive stop on ARM64.

**Checkpoint after T17:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T18: Local Kubernetes deployment

- [ ] Implement after permission.

**Reason:** Run the same platform contracts under Kubernetes scheduling.

**Tools:** kind, Helm. **Dependencies:** T17. **Scope:** 1–4 proposed files.

**Likely files:** infrastructure/helm/Chart.yaml; infrastructure/helm/values.yaml; infrastructure/helm/templates/workloads.yaml; docs/kubernetes-runbook.md.

**Acceptance:** Probes/resources/volumes explicit; smoke contracts pass; no cloud context targeted.

**Verification:** Render/lint manifests and test on the explicitly selected local context.

## T19: Autoscaling demonstration

- [ ] Implement after permission.

**Reason:** Show bounded replica growth and recovery under backlog.

**Tools:** HPA, metrics adapter or KEDA after selection. **Dependencies:** T18. **Scope:** 1–4 proposed files.

**Likely files:** infrastructure/helm/templates/scaling.yaml; tests/scenarios/scaling.py; docs/evidence/scaling.md.

**Acceptance:** 1/2/4 replicas preserve correctness; metrics and DB pool budgets constrain scaling.

**Verification:** Compare throughput, lag and connection use at fixed input.

**Checkpoint after T19:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T20: Load and accounting experiments

- [ ] Implement after permission.

**Reason:** Measure actual connections and reconcile all event outcomes.

**Tools:** Simulator, metrics, API load tool. **Dependencies:** T19. **Scope:** 1–4 proposed files.

**Likely files:** tests/scenarios/load.py; tools/reconcile_events.py; docs/evidence/load.md.

**Acceptance:** Publish profile/hardware/configuration; no unexplained event IDs; unachieved targets clearly marked.

**Verification:** Run approved stepped load and drain profiles.

## T21: Failure and security experiments

- [ ] Implement after permission.

**Reason:** Demonstrate behavior at each failure boundary.

**Tools:** Controlled process/network faults, pytest. **Dependencies:** T20. **Scope:** 1–4 proposed files.

**Likely files:** tests/scenarios/faults.py; tests/security/test_boundaries.py; docs/evidence/recovery.md.

**Acceptance:** AC-03, AC-05, AC-06 and AC-09 through AC-15 produce traceable evidence.

**Verification:** Inject the documented failures under a bounded demo load.

## T22: Backup and restore drill

- [ ] Implement after permission.

**Reason:** Prove recoverability from selected backup without damaging the only data copy.

**Tools:** PostgreSQL backup tools. **Dependencies:** T21. **Scope:** 1–4 proposed files.

**Likely files:** tools/backup.py; tools/restore.py; tests/scenarios/restore.py; docs/evidence/restore.md.

**Acceptance:** Isolated restore reconciles counts and reports measured RPO/RTO.

**Verification:** Restore a disposable dataset and compare immutable identities.

**Checkpoint after T22:** Review evidence, unresolved failures and the next stage scope with the user. Do not cross a stage boundary without permission.

## T23: Optional cloud implementation plan

- [ ] Implement after permission.

**Reason:** Turn cloud reference architecture into separately approved work only if requested.

**Tools:** Selected provider documentation and future IaC. **Dependencies:** T22 plus explicit cloud approval. **Scope:** 1–4 proposed files.

**Likely files:** docs/cloud-implementation-plan.md; docs/cloud-cost-estimate.md.

**Acceptance:** Provider/cost/quotas selected; new bounded implementation tasks and deployment gate documented.

**Verification:** Review plan and cost assumptions before any resource creation.

## T24: Portfolio walkthrough

- [ ] Implement after permission.

**Reason:** Explain only implemented and verified capabilities.

**Tools:** Markdown and sanitized evidence. **Dependencies:** T22; T23 not required. **Scope:** 1–4 proposed files.

**Likely files:** README.md; docs/demo.md; docs/runbook.md; docs/limitations.md.

**Acceptance:** Fresh reviewer can reproduce demo; limitations and evidence linked.

**Verification:** Follow documentation on a clean local environment.


## Stage 2 verification record

Checked 16 project Markdown files for local-link targets and balanced code fences; parsed both JSON examples. Reviewed all original requirements against local/cloud designs and AC-01 through AC-18. Reviewed the separate status path, broker/Redis durability gaps, commit receipts, bounded spools and partition-independent deduplication. Git whitespace validation passed. Changed project files are Markdown only. Mermaid diagrams received source review; no graphical renderer was run. No runtime acceptance test was run because implementation is not part of Stage 2.
