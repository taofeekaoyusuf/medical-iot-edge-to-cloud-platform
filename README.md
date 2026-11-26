# Medical IoT edge-to-cloud platform

A proposed Python platform for 25,000–50,000 simulated infusion pumps, with authenticated MQTT ingestion, asynchronous processing, device health, operational notifications, and an authorized API. All device data is synthetic; the project does not control real equipment or contain patient information.

**Status: Stage 2 design documentation. There is no runnable application yet.** Local implementation is the primary path. Cloud architecture is documented for a future decision; cloud code, accounts, provisioning, costs, and deployment are not authorized by this stage.

## Read the design

| Document | What it explains |
|---|---|
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

There are no install, run, migration, test, or deployment commands for the platform yet. Those will be added only in their approved implementation stages. Read the plan first; do not infer working features from the diagrams or examples.

The repository is public under [taofeekaoyusuf](https://github.com/taofeekaoyusuf/medical-iot-edge-to-cloud-platform), and is linked from [MyPortfolioProjects](https://github.com/taofeekaoyusuf/MyPortfolioProjects) as a submodule. See [AGENTS.md](AGENTS.md) for project rules. Stage 3 and later stages require new permission.
