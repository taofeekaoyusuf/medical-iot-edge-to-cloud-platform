# Acceptance criteria and evidence plan

All runtime items below are **proposed and untested**. These are targets to review before implementation, not claims that this machine can meet them. Any target change must be documented with evidence and approved, not silently weakened.

## Stage 2 completion

- Local and cloud designs have separate scope and deployment boundaries.
- Each required service has a responsibility, data owner and scaling strategy.
- MQTT identity, event formats, ordering, replay and deduplication are defined.
- API permissions, errors and lifecycle operations are defined.
- Recovery and security cases have observable outcomes.
- The implementation task list includes reasons, tools, dependencies, likely files and verification.
- Documentation links and examples pass static checks; no application or deployment code is added.

## Load profiles

| Profile | Device identities / actual connections | Event schedule | Measurement |
|---|---|---|---|
| Smoke | 100 / 100 | Heartbeat every 30 s | 5 min, complete-path correctness |
| Local demo | 1,000 / 1,000 | Heartbeat 30 s; operational 60 s | 5 min warmup + 15 min measured |
| Intermediate | 5,000 / 5,000 | Same | 5 min warmup + 30 min measured |
| Capacity | 25,000 then 50,000 / same actual connection target | Same; separate fault runs | Gradual ramp, 10 min warmup + 30 min measured if resources allow |
| Identity-only | 25,000–50,000 / explicitly reported smaller count | Same logical event schedule | Measures processing only; never reported as a connection test |

Spread phases deterministically across intervals. Proposed connect ramp: 100 new connections/second; adjust downward if observed limits require it and report the setting. At 25,000 devices the two periodic streams total 1,250 events/s; at 50,000 they total 2,500 events/s. This excludes receipts, diagnostics, retries and MQTT control packets. Heartbeats alone at 50,000 total about 1,667 events/s and 144 million/day. At 1 KiB per event, 2,500 events/s is about 8.6 GiB/hour of raw payload before database indexes and replication; short tests and retention budgets are essential.

## Functional and nonfunctional gates

| ID | Proposed acceptance target | Required evidence |
|---|---|---|
| AC-01 Identity | Every simulated device has a unique registered ID and unique valid credential in real-connection mode | Registry/connection counts, no shared credential shortcut |
| AC-02 Event validation | Valid examples accepted; all invalid boundary cases rejected with stable reasons | Contract tests per event type and field boundary |
| AC-03 Authorization | Invalid/expired certificates and cross-device publish/subscribe fail; viewer cannot mutate | Negative TLS/ACL/API tests |
| AC-04 Commit accounting | At demo load after 120 s drain: every generated eligible event is committed once or explicitly rejected (skipped scheduled samples are reported separately); no unexplained missing IDs | Reconciled event manifest and database unique keys |
| AC-05 Deduplication | Inject 10% same-content duplicates: one event and one semantic health effect per original; conflicting payload reuse rejected | DB counts and conflict tests |
| AC-06 Ordering | Older replay and delayed will never overwrite newer live state; boot conflicts rejected | Deterministic time/order tests |
| AC-07 Demo latency | Healthy 1,000-device run: ingress-to-commit p95 <=2 s and p99 <=5 s; API device lookup p95 <=500 ms at 10 requests/s | Histograms with sample counts; background load stated |
| AC-08 Connectivity | Offline detected within 100 s of last fresh heartbeat; delayed replay does not revive device | Controlled disconnect and stale-heartbeat test |
| AC-09 Reconnect | Demo fleet: >=99% reconnect within 120 s after broker becomes available; remaining clients accounted for | Connection histogram, jitter/backoff settings |
| AC-10 Recovery | With healthy resources, 60 s dependency outage drains backlog within 5 min after restoration at demo load | End-to-end accounting, memory remains within configured ceilings |
| AC-11 Scaling | At a fixed sustainable input, 1/2/4 processor replicas preserve correctness; publish throughput/latency curves and explain bottlenecks | Measured comparison, not assumed linear speedup |
| AC-12 Buffer limits | Hitting each configured limit produces backpressure/explicit loss counters; no silent pending-event trim | Limit-injection tests |
| AC-13 Notification | One open incident per device/rule; ACK does not resolve; recovery resolves once | Repeated and reordered event scenarios |
| AC-14 Monitoring | Dashboards show connections, lag, duplicates, storage and recovery; no device-ID labels | Dashboard captures and metric-label inspection |
| AC-15 Certificate lifecycle | Rotation works; revoked credential denied and existing-session enforcement demonstrated | Reconnect/rotation/revocation logs |
| AC-16 Restore | Restore the demo dataset within 15 min from a <=15-minute-old selected backup in an isolated drill | Measured RTO, backup age and event reconciliation |
| AC-17 Portability | Compose and local Kubernetes pass the same small contract suite | Separate run evidence and pinned image versions |
| AC-18 Capacity honesty | Report achieved stable connections at 25k/50k targets; if constrained, label target unverified and explain limit | Broker/client counts, resource measurements, zero extrapolated claims |

If capacity runs cannot fit this PC, AC-18 requires an honest limitation report, not a claim that the scale target passed. A later separately approved larger local machine or cloud experiment may provide that evidence.

## Cloud acceptance, deferred

Before deployment approval: choose provider, region, queue durability, broker availability model, identity, capacity and cost ceiling. After separately approved implementation: rerun contract, access, deduplication and recovery tests; verify private data endpoints, workload identities, backup restore, controlled rollout and cleanup. Neither Kubernetes manifests nor local tests alone validate cloud HA or availability-zone recovery.

## Verification status

Stage 2 supplies documentation only. All AC-01 through AC-18 and cloud runtime gates remain NOT RUN. Static review checks are recorded in [tasks/todo.md](../tasks/todo.md); implementation task completion must include actual evidence.
