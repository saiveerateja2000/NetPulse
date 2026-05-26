import json
import os
import socket
import subprocess
import threading
import time
from datetime import datetime, timezone
from ipaddress import ip_address
from statistics import mean
from typing import Dict, List, Optional

import dns.resolver
import psutil
import logging
import httpx
import ssl
from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from pydantic import BaseModel, field_validator
from ping3 import ping

app = FastAPI(title="NetPulse Collector Service")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "netpulse.telemetry")

# logging
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))
logger = logging.getLogger("collector")


@app.on_event("startup")
async def startup_event():
    logger.info("NetPulse Collector Service starting up...")
    logger.info(f"Kafka Bootstrap Servers: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC}")
    logger.info("Collector service is ready to accept monitoring requests")


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


class HTTPCheckRequest(BaseModel):
    target: str
    use_https: bool = False

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("target cannot be empty")
        return value


class BandwidthTestRequest(BaseModel):
    target: str
    test_size_mb: float = 10.0  # Size in MB

    @field_validator("target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("target cannot be empty")
        return value


class Collector:
    def __init__(self) -> None:
        self.sessions: Dict[str, SessionState] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()
        self.bytes_sent_last = psutil.net_io_counters().bytes_sent
        self.bytes_recv_last = psutil.net_io_counters().bytes_recv

    def _producer(self) -> Optional[KafkaProducer]:
        for attempt in range(5):
            try:
                logger.info(f"Attempting to create Kafka producer (attempt {attempt + 1}/5)")
                producer = KafkaProducer(
                    bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    api_version=(0, 10, 2),
                    max_block_ms=5000,
                    request_timeout_ms=5000,
                )
                logger.info("Kafka producer created successfully")
                return producer
            except Exception as e:
                logger.warning(f"Failed to create Kafka producer (attempt {attempt + 1}/5): {e}")
                if attempt < 4:
                    time.sleep(2)
        logger.error("Failed to create Kafka producer after 5 attempts")
        return None

    def start(self, target: str) -> None:
        with self.lock:
            existing = self.sessions.get(target)
            if existing and existing.running:
                return
            self.sessions[target] = SessionState(target=target, running=True, samples=[])

        logger.info("Starting collector for target %s", target)

        thread = threading.Thread(target=self._monitor_loop, args=(target,), daemon=True)
        self.threads[target] = thread
        thread.start()

    def stop(self, target: str) -> None:
        with self.lock:
            session = self.sessions.get(target)
            if session:
                session.running = False
        logger.info("Stopping collector for target %s", target)

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
        if not producer:
            logger.warning(f"Cannot start monitoring for {target}: Kafka producer unavailable")
            with self.lock:
                session = self.sessions.get(target)
                if session:
                    session.running = False
            return
            
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
                except Exception as e:
                    logger.warning("Failed to send metric to Kafka: %s", e)
            time.sleep(2)

        if producer:
            try:
                producer.flush(timeout=2)
                producer.close()
            except Exception:
                logger.exception("Error flushing/closing Kafka producer")

    def _collect_metrics(self, target: str, latency_history: List[float]) -> Dict:
        try:
            ping_value = ping(target, timeout=1)
        except Exception as e:
            logger.debug("Ping failed for %s: %s", target, e)
            ping_value = None
        latency_ms = round((ping_value or 0) * 1000, 2)
        packet_loss = 0.0 if ping_value is not None else 100.0

        start_dns = time.perf_counter()
        try:
            dns.resolver.resolve(target, "A")
            dns_lookup_time = round((time.perf_counter() - start_dns) * 1000, 2)
        except Exception as e:
            logger.debug("DNS lookup failed for %s: %s", target, e)
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
            logger.debug("Traceroute failed for %s", target)
            return "unavailable"

    def perform_traceroute(self, target: str) -> Dict:
        """Perform a full traceroute to the target"""
        try:
            logger.info(f"Starting traceroute for {target}")
            
            # Resolve target to IP first
            try:
                target_ip = socket.gethostbyname(target)
            except Exception as e:
                logger.error(f"Failed to resolve {target}: {e}")
                return {
                    "target": target,
                    "success": False,
                    "error": f"Failed to resolve target: {str(e)}",
                    "hops": [],
                    "total_hops": 0
                }
            
            hops = []
            max_hops = 30
            
            # Use traceroute command (Linux/Mac) or tracert (Windows)
            try:
                if os.name == 'nt':  # Windows
                    cmd = ['tracert', '-h', str(max_hops), target_ip]
                else:  # Linux/Mac
                    cmd = ['traceroute', '-m', str(max_hops), target_ip]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or 'traceroute' in line.lower() or 'tracing' in line.lower():
                        continue
                    
                    # Parse hop information
                    try:
                        parts = line.split()
                        if parts and parts[0].isdigit():
                            hop_num = int(parts[0])
                            
                            # Extract IP and latency
                            ip_match = None
                            latency_ms = None
                            
                            for part in parts[1:]:
                                if '(' in part and ')' in part:
                                    ip_match = part.strip('()')
                                elif 'ms' in part:
                                    try:
                                        latency_ms = float(part.replace('ms', '').strip())
                                    except:
                                        pass
                            
                            if ip_match or hop_num:
                                hops.append({
                                    "hop": hop_num,
                                    "ip": ip_match or "*",
                                    "latency_ms": latency_ms,
                                    "hostname": ip_match or "unknown"
                                })
                    except Exception as e:
                        logger.debug(f"Failed to parse hop line: {line}, {e}")
                        continue
                
                logger.info(f"Traceroute completed for {target}: {len(hops)} hops")
                return {
                    "target": target,
                    "target_ip": target_ip,
                    "success": True,
                    "hops": hops,
                    "total_hops": len(hops),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except subprocess.TimeoutExpired:
                logger.warning(f"Traceroute timeout for {target}")
                return {
                    "target": target,
                    "success": False,
                    "error": "Traceroute timeout",
                    "hops": hops,
                    "total_hops": len(hops)
                }
        except Exception as e:
            logger.error(f"Traceroute error for {target}: {e}")
            return {
                "target": target,
                "success": False,
                "error": str(e),
                "hops": [],
                "total_hops": 0
            }

    def perform_http_check(self, target: str, use_https: bool = False) -> Dict:
        """Check HTTP/HTTPS status code and response time"""
        try:
            logger.info(f"Starting HTTP check for {target}")
            
            protocol = "https" if use_https else "http"
            url = f"{protocol}://{target}"
            
            start_time = time.perf_counter()
            ssl_valid = None
            ssl_expiry_date = None
            status_code = None
            response_time_ms = None
            success = False
            error_message = None
            
            try:
                with httpx.Client(timeout=10, verify=True) as client:
                    response = client.get(url, follow_redirects=True)
                    response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    status_code = response.status_code
                    success = 200 <= status_code < 400
                    
                    # Check SSL certificate
                    if use_https:
                        try:
                            context = ssl.create_default_context()
                            with socket.create_connection((target, 443), timeout=5) as sock:
                                with context.wrap_socket(sock, server_hostname=target) as ssock:
                                    cert = ssock.getpeercert()
                                    ssl_valid = True
                                    if 'notAfter' in cert:
                                        ssl_expiry_date = cert['notAfter']
                        except Exception as ssl_err:
                            ssl_valid = False
                            logger.debug(f"SSL check failed for {target}: {ssl_err}")
                
            except httpx.TimeoutException:
                error_message = "HTTP request timeout"
                response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            except httpx.ConnectError as e:
                error_message = f"Connection failed: {str(e)}"
                response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            except Exception as e:
                error_message = str(e)
                response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            logger.info(f"HTTP check completed for {target}: {status_code}")
            return {
                "target": target,
                "url": url,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "ssl_valid": ssl_valid,
                "ssl_expiry_date": ssl_expiry_date,
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"HTTP check error for {target}: {e}")
            return {
                "target": target,
                "url": f"{'https' if use_https else 'http'}://{target}",
                "success": False,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def perform_bandwidth_test(self, target: str, test_size_mb: float = 10.0) -> Dict:
        """Perform a simple bandwidth test by downloading a file"""
        try:
            logger.info(f"Starting bandwidth test for {target} ({test_size_mb}MB)")
            
            # Use a test endpoint that serves data (we'll use httpbin or similar)
            # For this implementation, we'll simulate with a local approach
            test_url = f"http://{target}/api/random-data?size={int(test_size_mb * 1024 * 1024)}"
            
            start_time = time.perf_counter()
            bytes_downloaded = 0
            success = False
            error_message = None
            download_speed_mbps = None
            upload_speed_mbps = None
            
            try:
                with httpx.Client(timeout=60, verify=False) as client:
                    with client.stream('GET', test_url) as response:
                        if response.status_code == 200:
                            for chunk in response.iter_bytes(chunk_size=8192):
                                bytes_downloaded += len(chunk)
                
                elapsed_time = time.perf_counter() - start_time
                if elapsed_time > 0:
                    download_speed_mbps = round((bytes_downloaded / (1024 * 1024)) / elapsed_time, 2)
                    success = True
                    logger.info(f"Bandwidth test completed for {target}: {download_speed_mbps} Mbps")
                else:
                    error_message = "Test completed too quickly"
                    
            except Exception as e:
                elapsed_time = time.perf_counter() - start_time
                error_message = f"Bandwidth test failed: {str(e)}"
                logger.warning(f"Bandwidth test error for {target}: {e}")
                if bytes_downloaded > 0 and elapsed_time > 0:
                    download_speed_mbps = round((bytes_downloaded / (1024 * 1024)) / elapsed_time, 2)
            
            return {
                "target": target,
                "test_size_mb": test_size_mb,
                "bytes_transferred": bytes_downloaded,
                "download_speed_mbps": download_speed_mbps,
                "upload_speed_mbps": upload_speed_mbps,
                "test_duration_seconds": round(time.perf_counter() - start_time, 2),
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Bandwidth test error for {target}: {e}")
            return {
                "target": target,
                "test_size_mb": test_size_mb,
                "success": False,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


collector = Collector()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "collector"}


@app.get("/sessions")
def sessions() -> List[Dict]:
    return collector.list_sessions()


@app.post("/monitoring/start")
def start_monitoring(request: TargetRequest) -> Dict[str, str]:
    try:
        logger.info(f"Starting monitoring for target: {request.target}")
        collector.start(request.target)
        logger.info(f"Successfully started monitoring for target: {request.target}")
        return {"status": "started", "target": request.target}
    except Exception as e:
        logger.error(f"Failed to start monitoring for target {request.target}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}") from e


@app.post("/monitoring/stop")
def stop_monitoring(request: TargetRequest) -> Dict[str, str]:
    try:
        logger.info(f"Stopping monitoring for target: {request.target}")
        collector.stop(request.target)
        logger.info(f"Successfully stopped monitoring for target: {request.target}")
        return {"status": "stopped", "target": request.target}
    except Exception as e:
        logger.error(f"Failed to stop monitoring for target {request.target}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}") from e


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


# New diagnostic endpoints
@app.post("/diagnostics/traceroute")
def run_traceroute(request: TargetRequest) -> Dict:
    """Execute a full traceroute to the target"""
    try:
        logger.info(f"Traceroute requested for {request.target}")
        result = collector.perform_traceroute(request.target)
        return result
    except Exception as e:
        logger.error(f"Traceroute error: {e}")
        raise HTTPException(status_code=500, detail=f"Traceroute failed: {str(e)}") from e


@app.post("/diagnostics/http-check")
def run_http_check(request: HTTPCheckRequest) -> Dict:
    """Check HTTP/HTTPS status and response time"""
    try:
        logger.info(f"HTTP check requested for {request.target}")
        result = collector.perform_http_check(request.target, request.use_https)
        return result
    except Exception as e:
        logger.error(f"HTTP check error: {e}")
        raise HTTPException(status_code=500, detail=f"HTTP check failed: {str(e)}") from e


@app.post("/diagnostics/bandwidth-test")
def run_bandwidth_test(request: BandwidthTestRequest) -> Dict:
    """Perform a bandwidth test"""
    try:
        logger.info(f"Bandwidth test requested for {request.target}")
        result = collector.perform_bandwidth_test(request.target, request.test_size_mb)
        return result
    except Exception as e:
        logger.error(f"Bandwidth test error: {e}")
        raise HTTPException(status_code=500, detail=f"Bandwidth test failed: {str(e)}") from e
