# Medical IoT edge-to-cloud platform

A staged Python platform for 25,000–50,000 simulated infusion pumps, with authenticated MQTT ingestion, asynchronous processing, device health, operational notifications, and an authorized API. All device data is synthetic; the project does not control real equipment or contain patient information.

**Status: Stage 3 foundations implemented.** Python service scaffolds, strict telemetry validation and a bounded MQTT feasibility harness are runnable; domain services are not implemented yet. Local implementation is the primary path. Cloud architecture is documented for a future decision; cloud code, accounts, provisioning, costs, and deployment are not authorized by this stage.

## Read the design

| Document | What it explains |
|---|---|
| [Local development](docs/development.md) | Setup, checks, service scaffolds and MQTT experiment |
| [MQTT evidence](docs/evidence/mqtt-feasibility.md) | Measured 10/100/1,000-client results and limits |
| [Implementation plan](tasks/plan.md) | Stages, tools, reasons, dependencies, and approval gates |
| [Task checklist](tasks/todo.md) | Small implementation tasks and verification requirements |
| [Local architecture](docs/architecture/local.md) | Services, trust boundaries, Compose and local Kubernetes |
| [Cloud architecture](docs/architecture/cloud.md) | Portable deployment, Azure mapping, optional IoT Hub, migration gates |
| [Event contracts](docs/contracts/events.md) | MQTT topics, field definitions, examples, receipts, ordering |
| [API contracts](docs/contracts/api.md) | Endpoints, authorization, errors, pagination, registration |
| [Data and delivery](docs/data-and-delivery.md) | Ownership, transactions, deduplication, queues, retention |
| [Security](docs/security.md) | Certificates, ACLs, application identity, secret handling |
| [Operations](docs/operations.md) | Monitoring, scaling, outages, recovery, resource limits |
| [Acceptance criteria](docs/acceptance.md) | Proposed testable targets and evidence requirements |
| [Architecture decisions](docs/decisions/0001-platform-boundaries.md) | Rationale, alternatives, and consequences |
| [Source notes](docs/sources.md) | Official documentation used to check technical constraints |

## Getting started

Install the locked development environment and run the local checks:

```sh
uv sync --locked
make lint
make test-unit
make broker-up
make test
make broker-down
```

See [development](docs/development.md) for prerequisites, scaffold startup and experiment commands. The broker harness is deliberately loopback-only and has no device TLS/ACLs yet. Architecture diagrams describe the eventual platform, not completed capabilities.

The repository is public under [taofeekaoyusuf](https://github.com/taofeekaoyusuf/medical-iot-edge-to-cloud-platform), and is linked from [MyPortfolioProjects](https://github.com/taofeekaoyusuf/MyPortfolioProjects) as a submodule. See [AGENTS.md](AGENTS.md) for project rules. Stage 4 and later stages require new permission.
