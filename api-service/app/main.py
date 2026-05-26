import csv
import io
import os
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import List

import httpx
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

COLLECTOR_BASE_URL = os.getenv("COLLECTOR_BASE_URL", "http://localhost:8001")

app = FastAPI(title="NetPulse API Service")
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    """Return a context manager that yields a connection from a pool.

    The pool is created lazily on first use to avoid failing at import time.
    """
    global _DB_POOL
    if "_DB_POOL" not in globals() or _DB_POOL is None:
        try:
            _DB_POOL = SimpleConnectionPool(
                1,
                5,
                dbname=os.getenv("POSTGRES_DB", "netpulse"),
                user=os.getenv("POSTGRES_USER", "netpulse"),
                password=os.getenv("POSTGRES_PASSWORD", "netpulse"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
            )
        except Exception as exc:
            logger.exception("Failed to create DB connection pool: %s", exc)
            raise

    class _DBConnCtx:
        def __init__(self, pool: SimpleConnectionPool):
            self.pool = pool
            self.conn = None

        def __enter__(self):
            self.conn = self.pool.getconn()
            return self.conn

        def __exit__(self, exc_type, exc, tb):
            try:
                if self.conn is not None:
                    self.pool.putconn(self.conn)
            except Exception:
                pass

    return _DBConnCtx(_DB_POOL)


class TargetRequest(BaseModel):
    target: str

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("target cannot be empty")

        try:
            ip_address(value)
            return value
        except ValueError:
            pass

        if len(value.split(".")) < 2 or any(not part for part in value.split(".")):
            raise ValueError("target must be a valid IP address or domain")
        return value


class TargetState(BaseModel):
    target: str
    active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


TARGETS: dict[str, TargetState] = {}


@app.on_event("startup")
async def startup_event():
    logger.info("NetPulse API Service starting up...")
    logger.info(f"Collector Base URL: {COLLECTOR_BASE_URL}")
    logger.info("API service is ready to accept requests")


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/targets")
def list_targets() -> List[TargetState]:
    return list(TARGETS.values())


@app.post("/targets")
def add_target(request: TargetRequest):
    TARGETS.setdefault(request.target, TargetState(target=request.target))
    return {"status": "added", "target": request.target}


@app.post("/monitoring/start")
def start_monitoring(request: TargetRequest):
    if request.target not in TARGETS:
        TARGETS[request.target] = TargetState(target=request.target)

    try:
        logger.info(f"Starting monitoring for target: {request.target}")
        with httpx.Client(timeout=10) as client:
            response = client.post(f"{COLLECTOR_BASE_URL}/monitoring/start", json=request.model_dump())
        response.raise_for_status()
        logger.info(f"Successfully started monitoring for target: {request.target}")
    except httpx.HTTPError as exc:
        logger.error(f"Collector error when starting monitoring for {request.target}: {exc}")
        raise HTTPException(status_code=502, detail=f"Collector service error: {str(exc)}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error starting monitoring for {request.target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc

    TARGETS[request.target].active = True
    return {"status": "started", "target": request.target}


@app.post("/monitoring/stop")
def stop_monitoring(request: TargetRequest):
    try:
        logger.info(f"Stopping monitoring for target: {request.target}")
        with httpx.Client(timeout=10) as client:
            response = client.post(f"{COLLECTOR_BASE_URL}/monitoring/stop", json=request.model_dump())
        response.raise_for_status()
        logger.info(f"Successfully stopped monitoring for target: {request.target}")
    except httpx.HTTPError as exc:
        logger.error(f"Collector error when stopping monitoring for {request.target}: {exc}")
        raise HTTPException(status_code=502, detail=f"Collector service error: {str(exc)}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error stopping monitoring for {request.target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc

    if request.target in TARGETS:
        TARGETS[request.target].active = False

    return {"status": "stopped", "target": request.target}


@app.get("/metrics/live/{target}")
def get_live_metrics(target: str):
    try:
        logger.debug(f"Fetching live metrics for target: {target}")
        with httpx.Client(timeout=10) as client:
            response = client.get(f"{COLLECTOR_BASE_URL}/metrics/{target}")
        if response.status_code == 404:
            logger.warning(f"No live metrics found for target: {target}")
            raise HTTPException(status_code=404, detail="No live metric for target")
        response.raise_for_status()
        logger.debug(f"Successfully fetched live metrics for target: {target}")
        return response.json()
    except httpx.HTTPError as exc:
        if response.status_code != 404:
            logger.error(f"Collector error fetching metrics for {target}: {exc}")
            raise HTTPException(status_code=502, detail=f"Collector service error: {str(exc)}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error fetching metrics for {target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc


@app.get("/metrics/history/{target}")
def get_history(target: str, limit: int = 100):
    query = """
        SELECT target, latency_ms, packet_loss, jitter, dns_lookup_time,
               cpu_usage, memory_usage, bandwidth_usage, active_connections,
               traceroute_hops, ts
        FROM telemetry_metrics
        WHERE target = %s
        ORDER BY ts DESC
        LIMIT %s
    """

    try:
        logger.debug(f"Fetching history for target: {target} (limit: {limit})")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (target, limit))
                rows = cursor.fetchall()
        logger.debug(f"Successfully fetched {len(rows)} history records for target: {target}")
    except psycopg2.Error as exc:
        logger.error(f"Database error fetching history for {target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return [
        {
            "target": row[0],
            "latency_ms": row[1],
            "packet_loss": row[2],
            "jitter": row[3],
            "dns_lookup_time": row[4],
            "cpu_usage": row[5],
            "memory_usage": row[6],
            "bandwidth_usage": row[7],
            "active_connections": row[8],
            "traceroute_hops": row[9],
            "timestamp": row[10].isoformat(),
        }
        for row in rows
    ]


@app.get("/stream/events")
def stream_events():
    sessions_url = f"{COLLECTOR_BASE_URL}/sessions"
    try:
        logger.debug("Fetching stream events from collector...")
        with httpx.Client(timeout=10) as client:
            response = client.get(sessions_url)
        response.raise_for_status()
        logger.debug("Successfully fetched stream events")
        return {"topic": os.getenv("KAFKA_TOPIC", "netpulse.telemetry"), "sessions": response.json()}
    except httpx.HTTPError as exc:
        logger.error(f"Collector error fetching stream events: {exc}")
        raise HTTPException(status_code=502, detail=f"Collector service error: {str(exc)}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error fetching stream events: {exc}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc


@app.get("/reports/export/{target}")
def export_report(target: str):
    try:
        logger.info(f"Exporting report for target: {target}")
        history = get_history(target, limit=500)
        output = io.StringIO()
        fieldnames = list(history[0].keys()) if history else ["target", "latency_ms", "packet_loss", "jitter", "dns_lookup_time", "cpu_usage", "memory_usage", "bandwidth_usage", "active_connections", "traceroute_hops", "timestamp"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in history:
            writer.writerow(row)
        logger.info(f"Successfully exported report for target: {target} ({len(history)} records)")
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={target}-report.csv"},
        )
    except Exception as exc:
        logger.error(f"Error exporting report for {target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(exc)}") from exc
