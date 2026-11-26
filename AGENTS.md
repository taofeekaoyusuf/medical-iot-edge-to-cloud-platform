# Contributor and agent instructions

- Read the project README and applicable AGENTS.md before changing files.
- Respect the user's approved scope. Explain proposed actions and obtain permission before starting each new stage; approval for a stage covers its described actions.
- Do not begin the medical IoT project's Stage 2 until the user explicitly approves it.
- Keep credentials, private keys, local environment files, generated data, and patient data out of Git.
- Preserve existing files and user changes. Do not rename projects without permission.
- Use short-lived work branches and focused commits. Review staged changes before committing.
- Explain non-obvious decisions in comments or documentation and verify changes with appropriate checks.
- Report what changed, how it was verified, and unresolved limitations honestly.

## Medical IoT project constraints

- This project simulates infusion pumps using synthetic data only. It does not control real medical devices.
- All platform runtime, testing, monitoring, and deployment must run locally on the user's PC.
- Use local Docker and, in a later approved stage, local Kubernetes. Do not provision Azure, AKS, IoT Hub, or any cloud resources.
- GitHub is authorized for source hosting; it is not a platform runtime dependency.
- Cloud integration code is outside the current scope and requires separate approval.
- Target 25,000–50,000 simulated devices; distinguish device identities from actual concurrent MQTT connections and measured capacity.
- Application code, architecture, schemas, and infrastructure implementation await their respective stage approvals.
