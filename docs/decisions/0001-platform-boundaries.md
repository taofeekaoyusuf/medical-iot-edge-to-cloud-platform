# ADR-0001: Local implementation with a separate future cloud design

Status: Stage 3 foundation choices implemented and verified at bounded local scale. Later domain-service and cloud choices remain proposed and require their stage approvals.

## Context

The project must demonstrate device identity, concurrent MQTT connections, asynchronous processing, horizontal service scaling, monitoring and recovery. The available local machine is finite. The user has now authorized cloud architecture documentation while retaining explicit approval gates for implementation and deployment.

## Decision

Use Python services, Mosquitto, Redis Streams, PostgreSQL, Prometheus and Grafana in a local Docker Compose profile first, then demonstrate Kubernetes locally. Document a provider-neutral cloud topology and Azure mapping separately. Keep canonical event and API contracts independent of the transport deployment.

Choose FastAPI/Pydantic for application boundaries, SQLAlchemy/Alembic for persistence, and pytest/Ruff for focused validation in later stages. Use uv for reproducible Python environments. Paho MQTT is the initial client candidate because it exposes external-event-loop integration and manual incoming acknowledgement. The Stage 3 compatibility spike passed at up to 1,000 plaintext loopback clients; see [evidence](../evidence/mqtt-feasibility.md). TLS and larger-scale feasibility remain unverified. Do not create one network thread per simulated device. If the spike fails, evaluate an alternative under the same contracts and record a follow-up ADR.

## Alternatives

A single process would simplify local operation but conceal service boundaries. Cloud-first development would require resources the user does not currently have. IoT Hub-only ingress would reduce portability and change MQTT behavior. A replicated broker or persistent event log may be appropriate later, but adds complexity before the initial demonstration.

## Consequences

Microservices share one local database server but own distinct schemas. Cloud deployment remains optional and unimplemented. Local Kubernetes exercises scheduling and scaling, not physical fault-domain resilience. Scale claims require actual connection measurements. Dependency versions are pinned only after implementation-stage compatibility checks.

See [local](../architecture/local.md), [cloud](../architecture/cloud.md) and [task plan](../../tasks/plan.md).
