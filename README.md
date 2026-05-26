# NetPulse

NetPulse is a lightweight, open-source real-time network telemetry and analytics platform designed for local laptop execution (8GB RAM target).

## 🚀 Recent Updates (Fixed & Enhanced)

**All critical business logic issues have been fixed!** ✅

- ✅ Fixed "Failed to start monitoring" errors
- ✅ Fixed "Failed to stop monitoring" errors
- ✅ Added comprehensive error handling and logging
- ✅ Improved Kafka connection validation
- ✅ Enhanced timeouts and reliability
- ✅ Better user feedback in UI

See [FIXES_APPLIED.md](FIXES_APPLIED.md) for detailed changes.

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

See [guide.md](guide.md) for step-by-step instructions to build, run and test the stack with Docker Compose.

Docker Compose is self-contained; service environment values are defined in `docker-compose.yml`.

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

## Documentation

- [NEXT_STEPS.md](NEXT_STEPS.md) - Quick start after fixes
- [FIXES_APPLIED.md](FIXES_APPLIED.md) - Detailed technical changes
- [CODE_CHANGES_SUMMARY.md](CODE_CHANGES_SUMMARY.md) - Visual summary of code changes
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md) - Post-deployment verification

## Notes

- Spark runs in single-node local mode.
- Kafka topic is initialized with one partition.
- No Kubernetes or Hadoop dependencies are required.
