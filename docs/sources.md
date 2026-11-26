# Official source notes

These sources were consulted during Stage 2. They support technical constraints; the proposed thresholds, schemas, service boundaries and acceptance targets are project design choices. Recheck current documentation and pin compatible versions before implementation. No cloud account access was used.

| Source | Constraint checked |
|---|---|
| [Mosquitto configuration](https://mosquitto.org/man/mosquitto-conf-5.html) | TLS certificate authentication, ACL identity mapping, persistence settings |
| [Paho client API](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html) | Manual ACK and external event-loop support |
| [Redis Streams](https://redis.io/docs/latest/develop/data-types/streams/) | Consumer groups and pending-message reclaim |
| [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) | AOF fsync policy and durability limits |
| [PostgreSQL partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) | Partitioning and uniqueness constraints |
| [Kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/) | Local container-based Kubernetes |
| [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) | Metric-driven replica scaling |
| [Prometheus naming](https://prometheus.io/docs/practices/naming/) | Bounded label cardinality |
| [AKS baseline](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks/baseline-aks) | Reference cloud network and security topology |
| [IoT Hub MQTT](https://learn.microsoft.com/azure/iot-hub/iot-hub-mqtt-support) | Not a general-purpose MQTT broker |
| [IoT Hub quotas](https://learn.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-quotas-throttling) | Metering, throughput and throttling evaluation |
| [Azure Redis retirement guidance](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/retirement-faq) | Evaluate Managed Redis for a new future Azure design |

No free cloud capacity, concrete cloud price, clinical suitability or benchmark result is asserted by these documents.
