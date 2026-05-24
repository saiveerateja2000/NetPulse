# NetPulse Architecture

NetPulse uses a lightweight, local-first microservices architecture:

1. React frontend submits monitoring targets and renders live telemetry charts.
2. FastAPI API service validates targets and orchestrates monitor start/stop.
3. Collector service gathers network + system telemetry and emits events to Kafka.
4. PySpark Structured Streaming consumes Kafka events and writes telemetry rows to PostgreSQL.
5. Grafana reads PostgreSQL for operational dashboards.

This stack is optimized for personal laptops by using:

- single Kafka broker + 1 partition topic
- Spark `local[1]`
- Docker Compose orchestration only
