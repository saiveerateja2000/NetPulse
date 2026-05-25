import json
import os
import socket
import threading
import time
from datetime import datetime, timezone
from ipaddress import ip_address
from statistics import mean
from typing import Dict, List, Optional

import dns.resolver
import psutil
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from pydantic import BaseModel, field_validator
from ping3 import ping

app = FastAPI(title="NetPulse Collector Service")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "netpulse.telemetry")


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


class SessionState(BaseModel):
    target: str
    running: bool
    samples: List[Dict]


class Collector:
    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()
        self.bytes_sent_last = psutil.net_io_counters().bytes_sent
        self.bytes_recv_last = psutil.net_io_counters().bytes_recv

    def _producer(self) -> Optional[KafkaProducer]:
        for _ in range(5):
            try:
                return KafkaProducer(
                    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    api_version=(0, 10, 2),
                    max_block_ms=5000,
                    request_timeout_ms=5000,
                )
            except Exception:
                time.sleep(2)
        return None

    def start(self, target: str) -> None:
        with self.lock:
            existing = self.sessions.get(target)
            if existing and existing.running:
                return
            self.sessions[target] = SessionState(target=target, running=True, samples=[])

        thread = threading.Thread(target=self._monitor_loop, args=(target,), daemon=True)
        self.threads[target] = thread
        thread.start()

    def stop(self, target: str) -> None:
        with self.lock:
            session = self.sessions.get(target)
            if session:
                session.running = False

    def latest(self, target: str) -> Dict:
        session = self.sessions.get(target)
        if not session or not session.samples:
            raise HTTPException(status_code=404, detail="No telemetry found for target")
        return session.samples[-1]

    def list_sessions(self) -> List[Dict]:
        return [
            {
                "target": session.target,
                "running": session.running,
                "last_metric_at": session.samples[-1]["timestamp"] if session.samples else None,
            }
            for session in self.sessions.values()
        ]

    def _monitor_loop(self, target: str) -> None:
        producer = self._producer()
        latency_history: List[float] = []

        while True:
            with self.lock:
                session = self.sessions.get(target)
                if not session or not session.running:
                    break

            metric = self._collect_metrics(target, latency_history)
            with self.lock:
                current = self.sessions.get(target)
                if not current:
                    break
                current.samples.append(metric)
                if len(current.samples) > 300:
                    current.samples = current.samples[-300:]

            if producer:
                try:
                    producer.send(KAFKA_TOPIC, metric)
                except Exception:
                    pass
            time.sleep(2)

        if producer:
            try:
                producer.flush(timeout=2)
                producer.close()
            except Exception:
                pass

    def _collect_metrics(self, target: str, latency_history: List[float]) -> Dict:
        try:
            ping_value = ping(target, timeout=1)
        except Exception:
            ping_value = None
        latency_ms = round((ping_value or 0) * 1000, 2)
        packet_loss = 0.0 if ping_value is not None else 100.0

        start_dns = time.perf_counter()
        try:
            dns.resolver.resolve(target, "A")
            dns_lookup_time = round((time.perf_counter() - start_dns) * 1000, 2)
        except Exception:
            dns_lookup_time = 0.0

        latency_history.append(latency_ms)
        if len(latency_history) > 10:
            latency_history[:] = latency_history[-10:]

        jitter = round(abs(latency_history[-1] - latency_history[-2]), 2) if len(latency_history) > 1 else 0.0
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().percent

        io_now = psutil.net_io_counters()
        bandwidth_usage = max(
            0,
            ((io_now.bytes_sent - self.bytes_sent_last) + (io_now.bytes_recv - self.bytes_recv_last)) / 1024,
        )
        self.bytes_sent_last = io_now.bytes_sent
        self.bytes_recv_last = io_now.bytes_recv

        traceroute_hops = self._safe_traceroute(target)

        try:
            active_connections = len(psutil.net_connections(kind="inet"))
        except (psutil.AccessDenied, OSError, RuntimeError):
            active_connections = 0

        metric = {
            "target": target,
            "latency_ms": latency_ms,
            "packet_loss": packet_loss,
            "jitter": jitter,
            "dns_lookup_time": dns_lookup_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "bandwidth_usage": round(bandwidth_usage, 2),
            "active_connections": active_connections,
            "traceroute_hops": traceroute_hops,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return metric

    @staticmethod
    def _safe_traceroute(target: str) -> str:
        try:
            destination = socket.gethostbyname(target)
            return f"{destination} (single-hop estimate)"
        except Exception:
            return "unavailable"


collector = Collector()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "collector"}


@app.get("/sessions")
def sessions() -> List[Dict]:
    return collector.list_sessions()


@app.post("/monitoring/start")
def start_monitoring(request: TargetRequest) -> Dict[str, str]:
    collector.start(request.target)
    return {"status": "started", "target": request.target}


@app.post("/monitoring/stop")
def stop_monitoring(request: TargetRequest) -> Dict[str, str]:
    collector.stop(request.target)
    return {"status": "stopped", "target": request.target}


@app.get("/metrics/{target}")
def get_latest_metric(target: str) -> Dict:
    return collector.latest(target)


@app.get("/metrics/{target}/stats")
def get_target_stats(target: str) -> Dict:
    session = collector.sessions.get(target)
    if not session or not session.samples:
        raise HTTPException(status_code=404, detail="No telemetry found for target")

    samples = session.samples[-50:]
    return {
        "target": target,
        "sample_count": len(samples),
        "avg_latency_ms": round(mean(sample["latency_ms"] for sample in samples), 2),
        "avg_packet_loss": round(mean(sample["packet_loss"] for sample in samples), 2),
        "avg_jitter": round(mean(sample["jitter"] for sample in samples), 2),
    }
