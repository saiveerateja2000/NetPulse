# API Testing Guide - Diagnostic Endpoints

This guide provides copy-paste commands to test the new diagnostic features.

## Prerequisites

```bash
# Ensure services are running
docker-compose up -d
# Wait for services to be healthy (30-60 seconds)
```

---

## 1. Traceroute Tests

### Basic Traceroute
```bash
curl -X POST http://localhost:8000/diagnostics/traceroute \
  -H "Content-Type: application/json" \
  -d '{"target": "8.8.8.8"}'
```

### Traceroute to Domain
```bash
curl -X POST http://localhost:8000/diagnostics/traceroute \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'
```

### Get Traceroute History
```bash
curl http://localhost:8000/diagnostics/traceroute/example.com?limit=5
```

---

## 2. HTTP Check Tests

### HTTP Check (Plain)
```bash
curl -X POST http://localhost:8000/diagnostics/http-check \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "use_https": false}'
```

### HTTPS Check (with SSL validation)
```bash
curl -X POST http://localhost:8000/diagnostics/http-check \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "use_https": true}'
```

### Check Google
```bash
curl -X POST http://localhost:8000/diagnostics/http-check \
  -H "Content-Type: application/json" \
  -d '{"target": "google.com", "use_https": true}'
```

### Get HTTP Check History
```bash
curl http://localhost:8000/diagnostics/http-check/example.com?limit=10
```

---

## 3. Bandwidth Test

### Small Test (10MB - Fast)
```bash
curl -X POST http://localhost:8000/diagnostics/bandwidth-test \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "test_size_mb": 10}'
```

### Medium Test (50MB)
```bash
curl -X POST http://localhost:8000/diagnostics/bandwidth-test \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "test_size_mb": 50}'
```

### Get Bandwidth Test History
```bash
curl http://localhost:8000/diagnostics/bandwidth-test/example.com?limit=5
```

---

## Advanced Testing with Python

### Test All Features at Once
```python
import requests
import json

BASE_URL = "http://localhost:8000"
TARGET = "example.com"

# 1. Traceroute
print("Starting Traceroute...")
response = requests.post(
    f"{BASE_URL}/diagnostics/traceroute",
    json={"target": TARGET}
)
print(json.dumps(response.json(), indent=2))

# 2. HTTP Check
print("\nStarting HTTP Check...")
response = requests.post(
    f"{BASE_URL}/diagnostics/http-check",
    json={"target": TARGET, "use_https": True}
)
print(json.dumps(response.json(), indent=2))

# 3. Bandwidth Test
print("\nStarting Bandwidth Test...")
response = requests.post(
    f"{BASE_URL}/diagnostics/bandwidth-test",
    json={"target": TARGET, "test_size_mb": 10}
)
print(json.dumps(response.json(), indent=2))

# 4. Get Histories
print("\nRetrieving Histories...")
for endpoint in ["traceroute", "http-check", "bandwidth-test"]:
    response = requests.get(f"{BASE_URL}/diagnostics/{endpoint}/{TARGET}?limit=1")
    print(f"\n{endpoint.upper()} History:")
    print(json.dumps(response.json(), indent=2))
```

Save as `test_diagnostics.py` and run:
```bash
python test_diagnostics.py
```

---

## Monitoring Multiple Targets

### Bash Script for Multi-Target Monitoring
```bash
#!/bin/bash

TARGETS=("example.com" "google.com" "cloudflare.com" "8.8.8.8")
API="http://localhost:8000"

for target in "${TARGETS[@]}"; do
    echo "=========================================="
    echo "Testing: $target"
    echo "=========================================="
    
    echo -e "\n[HTTP Check]"
    curl -s -X POST "$API/diagnostics/http-check" \
      -H "Content-Type: application/json" \
      -d "{\"target\": \"$target\", \"use_https\": true}" | jq '.'
    
    echo -e "\n[Bandwidth Test]"
    curl -s -X POST "$API/diagnostics/bandwidth-test" \
      -H "Content-Type: application/json" \
      -d "{\"target\": \"$target\", \"test_size_mb\": 10}" | jq '.'
    
    echo -e "\n"
    sleep 2
done
```

Save and run:
```bash
chmod +x monitor.sh
./monitor.sh
```

---

## Performance Expectations

| Test | Timeout | Typical Duration |
|------|---------|------------------|
| Traceroute | 120s | 10-30s |
| HTTP Check | 30s | 1-5s |
| Bandwidth (10MB) | 300s | 5-30s |
| Bandwidth (50MB) | 300s | 20-60s |

---

## Expected Response Formats

### Success Response
```json
{
  "target": "example.com",
  "success": true,
  "timestamp": "2024-05-26T10:30:00Z",
  ...
}
```

### Error Response
```json
{
  "target": "unreachable.com",
  "success": false,
  "error_message": "Connection failed: [Errno -2] Name or service not known",
  "timestamp": "2024-05-26T10:30:00Z"
}
```

---

## Troubleshooting

### Traceroute Not Working
```bash
# Check if traceroute is available
which traceroute

# Install if missing (Linux)
sudo apt-get install iputils-tracepath traceroute

# Check if target is reachable
ping -c 1 example.com
```

### HTTP Check Fails
```bash
# Test directly
curl -v https://example.com

# Check DNS resolution
nslookup example.com
```

### Bandwidth Test Incomplete
```bash
# Try smaller test size
# Check network connectivity
iperf3 -c example.com
```

---

## Docker Compose Service Ports

- API Service: http://localhost:8000
- Collector Service: http://localhost:8001
- Grafana: http://localhost:3001
- PostgreSQL: localhost:5432
- Kafka: localhost:9092

---

## Real-World Monitoring Examples

### Example 1: Check All Services Every Minute
```bash
while true; do
  for target in "api.example.com" "web.example.com" "db.example.com"; do
    curl -s -X POST http://localhost:8000/diagnostics/http-check \
      -d "{\"target\": \"$target\", \"use_https\": true}" | \
      jq '{target: .target, status: .status_code, time: .response_time_ms}'
  done
  echo "---"
  sleep 60
done
```

### Example 2: Alert on Slow Response Times
```bash
curl -s -X POST http://localhost:8000/diagnostics/http-check \
  -d '{"target": "api.example.com", "use_https": true}' | \
  jq 'if .response_time_ms > 5000 then "SLOW: \(.response_time_ms)ms" else "OK" end'
```

### Example 3: Check Bandwidth Daily
```bash
# Add to crontab
0 9 * * * curl -X POST http://localhost:8000/diagnostics/bandwidth-test \
  -d '{"target": "speedtest.example.com", "test_size_mb": 100}' >> /var/log/bandwidth-test.log
```

---

## Logs

Check application logs:
```bash
# API Service
docker-compose logs -f api-service

# Collector Service
docker-compose logs -f collector-service

# Real-time tail
docker-compose logs -f --tail=50
```

---

**Happy Testing!** 🚀
