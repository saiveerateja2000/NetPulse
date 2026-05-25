# NetPulse — Quick Guide

This guide explains how to run NetPulse locally using Docker Compose, perform quick smoke tests, and run unit tests.

Prerequisites
- Docker & Docker Compose (or Docker Desktop)
- git
- Node (for local frontend build, optional)

Quick start (build & run)

```bash
# from repo root
docker compose up --build -d
# check running services
docker compose ps
# view logs (follow)
docker compose logs -f api-service collector-service frontend
```

Smoke tests (example requests)

```bash
# health
curl http://localhost:8000/health
curl http://localhost:8001/health

# list targets
curl http://localhost:8000/targets

# add a target
curl -X POST http://localhost:8000/targets \
  -H 'Content-Type: application/json' \
  -d '{"target":"example.com"}'

# start monitoring (collector will start producing events)
curl -X POST http://localhost:8000/monitoring/start \
  -H 'Content-Type: application/json' \
  -d '{"target":"example.com"}'

# live and history
curl http://localhost:8000/metrics/live/example.com
curl http://localhost:8000/metrics/history/example.com

# stream events
curl http://localhost:8000/stream/events
```

Notes
- Live metrics may return 404 until the collector produces the first metric for a target.
- The frontend is available at `http://localhost:3000` and Grafana at `http://localhost:3001` (default `admin/admin`).

Running tests

```bash
# API unit tests
cd api-service
pip install -r requirements.txt -r requirements-dev.txt
PYTHONPATH=. pytest -q
```

Build frontend (optional)

```bash
cd frontend
npm ci
npm run build
```

Removing Makefile

The repository previously included a `Makefile` with convenience targets for `up`, `down`, `api-test` and `frontend-build`.
This project uses Docker Compose directly; the `Makefile` has been removed to avoid stale references. The commands above are the recommended replacements.

Troubleshooting
- If a service fails to start, inspect logs: `docker compose logs <service>`.
- Postgres init SQL runs from `postgres/init.sql` on first start; check Postgres logs for migration errors.
- Kafka/Zookeeper container logs may show non-fatal warnings; they can usually be ignored unless topics fail to initialize.

If you'd like, I can:
- add a minimal `Makefile` that wraps the Docker commands, or
- create a short `CONTRIBUTING.md` with development workflows.
