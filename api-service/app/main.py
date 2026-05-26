import csv
import io
import os
import json
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from typing import List, Optional
from uuid import UUID

import httpx
import psycopg2
from psycopg2.pool import SimpleConnectionPool
import dns.resolver
import logging
from fastapi import FastAPI, HTTPException, Query
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


# DNS Resolution models
class DNSResolution(BaseModel):
    query: str  # Original input (IP or domain)
    is_ip: bool  # Whether input was already an IP
    resolved_ips: List[str]  # List of resolved IPs
    primary_ip: str  # First/primary resolved IP
    resolver_used: str = "nslookup"  # DNS resolver type
    query_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# New Session models
class SessionCreate(BaseModel):
    target: str
    description: Optional[str] = None
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    description: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # active, paused, stopped


class SessionResponse(BaseModel):
    session_id: str
    target: str
    status: str
    started_at: datetime
    stopped_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class SessionMetrics(BaseModel):
    avg_latency_ms: Optional[float]
    avg_packet_loss: Optional[float]
    avg_jitter: Optional[float]
    min_latency_ms: Optional[float]
    max_latency_ms: Optional[float]
    total_records: int


class SessionStats(BaseModel):
    session_id: str
    target: str
    duration_seconds: int
    status: str
    metrics: SessionMetrics


TARGETS: dict[str, TargetState] = {}


@app.on_event("startup")
async def startup_event():
    logger.info("NetPulse API Service starting up...")
    logger.info(f"Collector Base URL: {COLLECTOR_BASE_URL}")
    logger.info("API service is ready to accept requests")


@app.get("/health")
def health():
    return {"status": "ok", "service": "api"}


@app.get("/resolve/{target}")
def resolve_target(target: str) -> DNSResolution:
    """Resolve a domain name to IP address(es) using DNS lookup
    
    Returns:
    - If input is an IP: returns as-is
    - If input is a domain: resolves to IP(s) and returns all results
    """
    try:
        logger.info(f"Resolving target: {target}")
        target = target.strip().lower()
        
        # Check if target is already an IP address
        try:
            resolved_ip = str(ip_address(target))
            logger.info(f"Target {target} is already an IP address")
            return DNSResolution(
                query=target,
                is_ip=True,
                resolved_ips=[resolved_ip],
                primary_ip=resolved_ip,
                resolver_used="ip_validation"
            )
        except ValueError:
            # Not an IP, so resolve as domain
            pass
        
        # Resolve domain using dns.resolver
        try:
            answers = dns.resolver.resolve(target, 'A')
            resolved_ips = [str(rdata) for rdata in answers]
            
            logger.info(f"Successfully resolved {target} to {resolved_ips}")
            return DNSResolution(
                query=target,
                is_ip=False,
                resolved_ips=resolved_ips,
                primary_ip=resolved_ips[0] if resolved_ips else None,
                resolver_used="nslookup"
            )
        except dns.resolver.NXDOMAIN:
            logger.warning(f"Domain not found: {target}")
            raise HTTPException(status_code=404, detail=f"Domain '{target}' not found (NXDOMAIN)")
        except dns.resolver.NoAnswer:
            logger.warning(f"No A records for domain: {target}")
            raise HTTPException(status_code=404, detail=f"No A records found for '{target}'")
        except dns.exception.DNSException as dns_err:
            logger.error(f"DNS resolution error for {target}: {dns_err}")
            raise HTTPException(status_code=503, detail=f"DNS resolution failed: {str(dns_err)}")
            
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error resolving {target}: {exc}")
        raise HTTPException(status_code=500, detail=f"Resolution error: {str(exc)}")


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


# ==================== NEW SESSION MANAGEMENT ENDPOINTS ====================

@app.post("/sessions")
def create_session(request: SessionCreate) -> SessionResponse:
    """Create a new monitoring session"""
    try:
        query = """
            INSERT INTO monitoring_sessions (target, description, notes)
            VALUES (%s, %s, %s)
            RETURNING session_id, target, status, started_at, stopped_at, paused_at, 
                     resumed_at, description, notes, created_at
        """
        
        logger.info(f"Creating session for target: {request.target}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (request.target, request.description, request.notes))
                row = cursor.fetchone()
                conn.commit()
        
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        logger.info(f"Session created successfully: {row[0]}")
        return SessionResponse(
            session_id=str(row[0]),
            target=row[1],
            status=row[2],
            started_at=row[3],
            stopped_at=row[4],
            paused_at=row[5],
            resumed_at=row[6],
            description=row[7],
            notes=row[8],
            created_at=row[9]
        )
    except psycopg2.Error as exc:
        logger.error(f"Database error creating session: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/sessions")
def list_sessions(target: Optional[str] = None, status: Optional[str] = None) -> List[SessionResponse]:
    """List all monitoring sessions with optional filtering"""
    try:
        query = "SELECT session_id, target, status, started_at, stopped_at, paused_at, resumed_at, description, notes, created_at FROM monitoring_sessions WHERE 1=1"
        params = []
        
        if target:
            query += " AND target = %s"
            params.append(target)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        logger.debug(f"Listing sessions with filters - target: {target}, status: {status}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        
        logger.debug(f"Found {len(rows)} sessions")
        return [
            SessionResponse(
                session_id=str(row[0]),
                target=row[1],
                status=row[2],
                started_at=row[3],
                stopped_at=row[4],
                paused_at=row[5],
                resumed_at=row[6],
                description=row[7],
                notes=row[8],
                created_at=row[9]
            )
            for row in rows
        ]
    except psycopg2.Error as exc:
        logger.error(f"Database error listing sessions: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/sessions/{session_id}")
def get_session(session_id: str) -> SessionResponse:
    """Get a specific session by ID"""
    try:
        query = "SELECT session_id, target, status, started_at, stopped_at, paused_at, resumed_at, description, notes, created_at FROM monitoring_sessions WHERE session_id = %s"
        
        logger.debug(f"Fetching session: {session_id}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (session_id,))
                row = cursor.fetchone()
        
        if not row:
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=str(row[0]),
            target=row[1],
            status=row[2],
            started_at=row[3],
            stopped_at=row[4],
            paused_at=row[5],
            resumed_at=row[6],
            description=row[7],
            notes=row[8],
            created_at=row[9]
        )
    except psycopg2.Error as exc:
        logger.error(f"Database error fetching session: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.put("/sessions/{session_id}")
def update_session(session_id: str, request: SessionUpdate) -> SessionResponse:
    """Update a monitoring session"""
    try:
        updates = []
        params = []
        
        if request.description is not None:
            updates.append("description = %s")
            params.append(request.description)
        
        if request.notes is not None:
            updates.append("notes = %s")
            params.append(request.notes)
        
        if request.status is not None:
            updates.append("status = %s")
            params.append(request.status)
            # Handle status-specific timestamps
            if request.status == "stopped":
                updates.append("stopped_at = %s")
                params.append(datetime.now(timezone.utc))
            elif request.status == "paused":
                updates.append("paused_at = %s")
                params.append(datetime.now(timezone.utc))
            elif request.status == "active":
                updates.append("resumed_at = %s")
                params.append(datetime.now(timezone.utc))
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(session_id)
        query = f"UPDATE monitoring_sessions SET {', '.join(updates)} WHERE session_id = %s RETURNING session_id, target, status, started_at, stopped_at, paused_at, resumed_at, description, notes, created_at"
        
        logger.info(f"Updating session: {session_id}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                conn.commit()
        
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"Session updated successfully: {session_id}")
        return SessionResponse(
            session_id=str(row[0]),
            target=row[1],
            status=row[2],
            started_at=row[3],
            stopped_at=row[4],
            paused_at=row[5],
            resumed_at=row[6],
            description=row[7],
            notes=row[8],
            created_at=row[9]
        )
    except psycopg2.Error as exc:
        logger.error(f"Database error updating session: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a monitoring session and its metrics"""
    try:
        logger.info(f"Deleting session: {session_id}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Get session details first
                cursor.execute("SELECT target FROM monitoring_sessions WHERE session_id = %s", (session_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Delete session and associated metrics (cascade)
                cursor.execute("DELETE FROM monitoring_sessions WHERE session_id = %s", (session_id,))
                conn.commit()
        
        logger.info(f"Session deleted successfully: {session_id}")
        return {"status": "deleted", "session_id": session_id}
    except psycopg2.Error as exc:
        logger.error(f"Database error deleting session: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/sessions/{session_id}/stats")
def get_session_stats(session_id: str) -> SessionStats:
    """Get statistics for a session"""
    try:
        query = """
            SELECT 
                ms.session_id, ms.target, ms.status, ms.started_at, ms.stopped_at,
                COUNT(tm.id) as total_records,
                AVG(tm.latency_ms) as avg_latency,
                AVG(tm.packet_loss) as avg_packet_loss,
                AVG(tm.jitter) as avg_jitter,
                MIN(tm.latency_ms) as min_latency,
                MAX(tm.latency_ms) as max_latency
            FROM monitoring_sessions ms
            LEFT JOIN telemetry_metrics tm ON ms.session_id = tm.session_id
            WHERE ms.session_id = %s
            GROUP BY ms.session_id, ms.target, ms.status, ms.started_at, ms.stopped_at
        """
        
        logger.debug(f"Fetching stats for session: {session_id}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (session_id,))
                row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_id_val, target, status, started_at, stopped_at = row[0:5]
        total_records = row[5]
        avg_latency = row[6]
        avg_packet_loss = row[7]
        avg_jitter = row[8]
        min_latency = row[9]
        max_latency = row[10]
        
        # Calculate duration
        end_time = stopped_at if stopped_at else datetime.now(timezone.utc)
        duration = (end_time - started_at).total_seconds()
        
        return SessionStats(
            session_id=str(session_id_val),
            target=target,
            duration_seconds=int(duration),
            status=status,
            metrics=SessionMetrics(
                avg_latency_ms=avg_latency,
                avg_packet_loss=avg_packet_loss,
                avg_jitter=avg_jitter,
                min_latency_ms=min_latency,
                max_latency_ms=max_latency,
                total_records=total_records
            )
        )
    except psycopg2.Error as exc:
        logger.error(f"Database error fetching session stats: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc


@app.get("/sessions/{session_id}/export")
def export_session(session_id: str, format: str = Query("csv", regex="^(csv|json)$")):
    """Export session data in CSV or JSON format"""
    try:
        query = """
            SELECT target, latency_ms, packet_loss, jitter, dns_lookup_time,
                   cpu_usage, memory_usage, bandwidth_usage, active_connections,
                   traceroute_hops, ts
            FROM telemetry_metrics
            WHERE session_id = %s
            ORDER BY ts DESC
        """
        
        logger.info(f"Exporting session {session_id} as {format}")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (session_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    raise HTTPException(status_code=404, detail="No data found for session")
                
                # Get session info
                cursor.execute("SELECT target FROM monitoring_sessions WHERE session_id = %s", (session_id,))
                session_row = cursor.fetchone()
                
                if not session_row:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                target = session_row[0]
        
        data = [
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
        
        if format == "json":
            output = json.dumps(data, indent=2)
            media_type = "application/json"
            filename = f"session-{session_id}-export.json"
        else:  # csv
            output = io.StringIO()
            fieldnames = list(data[0].keys()) if data else []
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
            output = output.getvalue()
            media_type = "text/csv"
            filename = f"session-{session_id}-export.csv"
        
        logger.info(f"Session {session_id} exported successfully ({len(data)} records)")
        return StreamingResponse(
            iter([output]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except psycopg2.Error as exc:
        logger.error(f"Database error exporting session: {exc}")
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
