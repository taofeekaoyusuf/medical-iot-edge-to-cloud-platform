# Contributor and agent instructions

- Read the project README and applicable AGENTS.md before changing files.
- Respect the user's approved scope. Explain proposed actions and obtain permission before starting each new stage; approval for a stage covers its described actions.
- Stage 3 foundations, event validators and bounded local MQTT experiments (at most 1,000 clients) are approved. Obtain explicit permission before Stage 4 or any later stage.
- Keep credentials, private keys, local environment files, generated data, and patient data out of Git.
- Preserve existing files and user changes. Do not rename projects without permission.
- Use short-lived work branches and focused commits. Review staged changes before committing.
- Explain non-obvious decisions in comments or documentation and verify changes with appropriate checks.
- Report what changed, how it was verified, and unresolved limitations honestly.

## Medical IoT project constraints

- This project simulates infusion pumps using synthetic data only. It does not control real medical devices.
- Local runtime, testing, monitoring and deployment remain the primary implementation target. Future cloud architecture documentation is authorized; cloud implementation and deployment are not.
- Use local Docker and, in a later approved stage, local Kubernetes. Do not provision Azure, AKS, IoT Hub, or any cloud resources.
- GitHub is authorized for source hosting; it is not a platform runtime dependency.
- Cloud integration code is outside the current scope and requires separate approval.
- Target 25,000–50,000 simulated devices; distinguish device identities from actual concurrent MQTT connections and measured capacity.
- Stage 2 defines local/cloud architecture. Stage 3 implements only the Python foundation, event validation, service scaffolds and isolated local MQTT feasibility harness. Domain services and cloud implementation await later stage approvals.
