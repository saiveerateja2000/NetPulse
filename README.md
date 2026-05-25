# NetPulse

NetPulse is a lightweight, open-source real-time network telemetry and analytics platform designed for local laptop execution (8GB RAM target).

## Tech Stack

- **Frontend**: React, Tailwind CSS, Recharts
- **Backend APIs**: FastAPI, Uvicorn, Pydantic
- **Collector**: Python, psutil, ping3, scapy
- **Streaming**: Apache Kafka + Zookeeper
- **Processing**: PySpark Structured Streaming
- **Storage**: PostgreSQL
- **Dashboards**: Grafana
- **Orchestration**: Docker Compose

## Project Structure

- `frontend/`
- `collector-service/`
- `spark-streaming-service/`
- `api-service/`
- `grafana/`
- `postgres/`
- `kafka/`
- `docs/`

## Run Locally

```bash
make up
```

Endpoints:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000/docs`
- Collector: `http://localhost:8001/docs`
- Grafana: `http://localhost:3001` (`admin/admin`)

## Core Features

- Add monitoring target (IP/domain)
- Start/stop monitoring sessions
- Live network metrics (latency, packet loss, jitter)
- CPU/memory/bandwidth + active connection telemetry
- Kafka stream event visibility
- Historical metric storage in PostgreSQL
- Export CSV reports per target

## Notes

- Spark runs in single-node local mode.
- Kafka topic is initialized with one partition.
- No Kubernetes or Hadoop dependencies are required.
