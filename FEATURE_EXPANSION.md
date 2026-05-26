# NetPulse Feature Expansion - Network Diagnostics Suite

**Branch**: `feature/network-diagnostics-expansion`

This expansion adds three powerful network diagnostic capabilities to NetPulse, enabling comprehensive network troubleshooting, uptime monitoring, and performance analysis.

---

## 🎯 New Features Overview

### 1. **Traceroute (Full Path Discovery)**
Trace the complete network path to your target with hop-by-hop latency analysis.

**Use Cases**:
- Identify network bottlenecks in the path
- Detect where latency is introduced
- Understand network topology
- Diagnose routing issues

**Request**:
```bash
curl -X POST http://localhost:8000/diagnostics/traceroute \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com"}'
```

**Response**:
```json
{
  "target": "example.com",
  "target_ip": "93.184.216.34",
  "success": true,
  "hops": [
    {
      "hop": 1,
      "ip": "192.168.1.1",
      "latency_ms": 2.5,
      "hostname": "router.local"
    },
    {
      "hop": 2,
      "ip": "10.0.0.1",
      "latency_ms": 5.8,
      "hostname": "gateway.isp"
    },
    {
      "hop": 3,
      "ip": "93.184.216.34",
      "latency_ms": 25.3,
      "hostname": "example.com"
    }
  ],
  "total_hops": 3,
  "timestamp": "2024-05-26T10:30:00Z"
}
```

**Retrieve History**:
```bash
curl http://localhost:8000/diagnostics/traceroute/example.com?limit=10
```

---

### 2. **HTTP Status Checks**
Monitor website/API availability, response times, and SSL certificate validity.

**Use Cases**:
- Uptime monitoring for websites and APIs
- Performance tracking (response time)
- SSL certificate expiry alerts
- Service dependency monitoring
- Load balancer health checks

**Request**:
```bash
curl -X POST http://localhost:8000/diagnostics/http-check \
  -H "Content-Type: application/json" \
  -d '{"target": "example.com", "use_https": true}'
```

**Response**:
```json
{
  "target": "example.com",
  "url": "https://example.com",
  "status_code": 200,
  "response_time_ms": 245.67,
  "ssl_valid": true,
  "ssl_expiry_date": "2025-06-15",
  "success": true,
  "error_message": null,
  "timestamp": "2024-05-26T10:30:00Z"
}
```

**Failed Response Example**:
```json
{
  "target": "unreachable.com",
  "url": "https://unreachable.com",
  "status_code": null,
  "response_time_ms": 5012.34,
  "ssl_valid": false,
  "ssl_expiry_date": null,
  "success": false,
  "error_message": "Connection timeout after 10s",
  "timestamp": "2024-05-26T10:30:00Z"
}
```

**Retrieve History**:
```bash
curl http://localhost:8000/diagnostics/http-check/example.com?limit=20
```

---

### 3. **Bandwidth Quick Test**
Test download speeds and measure throughput to your target.

**Use Cases**:
- Measure network throughput
- Monitor ISP speed compliance
- Identify bandwidth degradation
- Test multi-region connectivity
- Validate network upgrades

**Request**:
```bash
curl -X POST http://localhost:8000/diagnostics/bandwidth-test \
  -H "Content-Type: application/json" \
  -d '{"target": "speedtest.example.com", "test_size_mb": 50}'
```

**Response**:
```json
{
  "target": "speedtest.example.com",
  "test_size_mb": 50,
  "bytes_transferred": 52428800,
  "download_speed_mbps": 125.45,
  "upload_speed_mbps": null,
  "test_duration_seconds": 3.34,
  "success": true,
  "error_message": null,
  "timestamp": "2024-05-26T10:30:00Z"
}
```

**Retrieve History**:
```bash
curl http://localhost:8000/diagnostics/bandwidth-test/speedtest.example.com?limit=10
```

---

## 📊 Database Schema

### traceroute_results
```sql
- id (SERIAL PRIMARY KEY)
- target (VARCHAR) - The target IP/domain
- hops (JSONB) - Array of hop information
- total_hops (INTEGER)
- completed_at (TIMESTAMPTZ)
- success (BOOLEAN)
```

### http_check_results
```sql
- id (SERIAL PRIMARY KEY)
- target (VARCHAR)
- url (VARCHAR)
- status_code (INTEGER)
- response_time_ms (DOUBLE PRECISION)
- ssl_valid (BOOLEAN)
- ssl_expiry_date (VARCHAR)
- success (BOOLEAN)
- error_message (TEXT)
- checked_at (TIMESTAMPTZ)
```

### bandwidth_test_results
```sql
- id (SERIAL PRIMARY KEY)
- target (VARCHAR)
- test_size_mb (DOUBLE PRECISION)
- download_speed_mbps (DOUBLE PRECISION)
- upload_speed_mbps (DOUBLE PRECISION)
- test_duration_seconds (DOUBLE PRECISION)
- success (BOOLEAN)
- error_message (TEXT)
- tested_at (TIMESTAMPTZ)
```

---

## 🔌 API Endpoints Reference

### Collector Service (Internal)
Endpoints exposed by `collector-service:8001`:
- `POST /diagnostics/traceroute` - Execute traceroute
- `POST /diagnostics/http-check` - Execute HTTP check
- `POST /diagnostics/bandwidth-test` - Execute bandwidth test

### API Service (External)
Endpoints exposed by `api-service:8000`:
- `POST /diagnostics/traceroute` - Trigger and save traceroute
- `POST /diagnostics/http-check` - Trigger and save HTTP check
- `POST /diagnostics/bandwidth-test` - Trigger and save bandwidth test
- `GET /diagnostics/traceroute/{target}` - Retrieve history
- `GET /diagnostics/http-check/{target}` - Retrieve history
- `GET /diagnostics/bandwidth-test/{target}` - Retrieve history

---

## ⏱️ Timeout & Performance

| Feature | Timeout | Typical Duration |
|---------|---------|------------------|
| Traceroute | 120s | 10-30s |
| HTTP Check | 30s | 1-5s |
| Bandwidth Test (10MB) | 300s | 5-30s |

---

## 💡 Recommended Usage Patterns

### 1. Real-Time Diagnostics
Run diagnostics directly via REST API for immediate troubleshooting:
```bash
# Quick availability check
curl -X POST http://localhost:8000/diagnostics/http-check \
  -d '{"target": "api.example.com", "use_https": true}'

# Understand network path
curl -X POST http://localhost:8000/diagnostics/traceroute \
  -d '{"target": "api.example.com"}'
```

### 2. Scheduled Monitoring
Combine with cron/scheduler to run tests periodically:
```bash
# Every 5 minutes check status
0 */5 * * * curl -X POST http://localhost:8000/diagnostics/http-check \
  -d '{"target": "service.example.com", "use_https": true}'
```

### 3. Multi-Target Monitoring
Monitor multiple services/regions:
```bash
for target in "us.example.com" "eu.example.com" "asia.example.com"; do
  curl -X POST http://localhost:8000/diagnostics/http-check \
    -d "{\"target\": \"$target\", \"use_https\": true}"
done
```

---

## 🛠️ Integration with Existing Features

All diagnostics data is stored in PostgreSQL and can be:
- **Exported to CSV**: Via existing export endpoints
- **Queried Directly**: Via SQL for custom analysis
- **Viewed in Grafana**: Create dashboards using Grafana queries
- **Combined with Metrics**: Correlate with existing latency/packet loss data

---

## 📝 Implementation Notes

### Technical Details

1. **Traceroute Implementation**:
   - Uses system `traceroute` command (Linux/Mac) or `tracert` (Windows)
   - Parses standard output to extract hops and latency
   - Returns cleaned hop information with IP resolution

2. **HTTP Check Implementation**:
   - Uses `httpx` with SSL verification
   - Follows redirects (up to default limit)
   - Validates SSL certificates separately
   - Handles timeouts gracefully

3. **Bandwidth Test Implementation**:
   - Downloads test file to measure speed
   - Uses 8KB chunks for streaming
   - Calculates throughput based on bytes and elapsed time
   - Handles partial transfers

### Error Handling
All endpoints include:
- Comprehensive error messages
- Success/failure flags
- Timeout protection
- Graceful degradation

### Database Persistence
- All results automatically saved to PostgreSQL
- Indexed by target and timestamp for fast queries
- Historical data retention for trend analysis
- JSON support for complex hop information

---

## 🚀 Next Steps / Future Enhancements

1. **Alerting System**
   - Send alerts on status changes
   - Webhook integrations
   - Slack/PagerDuty notifications

2. **Web UI Dashboard**
   - Real-time diagnostics interface
   - Historical trend charts
   - Target status overview

3. **Advanced Features**
   - MTU path discovery
   - Port scanning capabilities
   - Geolocation mapping
   - Custom test endpoints

4. **Multi-Tenant Support**
   - User accounts and authentication
   - Role-based access control
   - Private test endpoints

---

## 📖 Example Workflows

### Workflow 1: Debug High Latency to Service
```bash
# Step 1: Check if service is online
curl -X POST http://localhost:8000/diagnostics/http-check \
  -d '{"target": "api.example.com", "use_https": true}'

# Step 2: Trace the path to identify bottleneck
curl -X POST http://localhost:8000/diagnostics/traceroute \
  -d '{"target": "api.example.com"}'

# Step 3: Look at historical data to see if pattern
curl http://localhost:8000/diagnostics/http-check/api.example.com?limit=20
```

### Workflow 2: Verify ISP Speed Compliance
```bash
# Weekly bandwidth test
curl -X POST http://localhost:8000/diagnostics/bandwidth-test \
  -d '{"target": "speedtest.example.com", "test_size_mb": 100}'

# Check history to ensure consistent speeds
curl http://localhost:8000/diagnostics/bandwidth-test/speedtest.example.com?limit=52
```

### Workflow 3: Monitor Multiple Services
```bash
# Create a loop for multi-service monitoring
services=("service1.example.com" "service2.example.com" "service3.example.com")

for service in "${services[@]}"; do
  echo "Checking $service"
  curl -X POST http://localhost:8000/diagnostics/http-check \
    -d "{\"target\": \"$service\", \"use_https\": true}"
done
```

---

## 📊 Real-World Use Cases

### DevOps / SRE Teams
- Rapid incident diagnostics
- Service dependency validation
- Multi-region health checks
- Performance regression detection

### ISPs / Telecom
- Customer self-service diagnostics
- Speed test aggregation
- Network quality metrics
- Troubleshooting automation

### Distributed Teams
- Remote office connectivity checks
- VPN quality monitoring
- Internet stability validation
- Location-based performance analysis

### Educational Institutions
- Student networking labs
- Network behavior studies
- Internet infrastructure teaching
- Research data collection

---

## ✅ Testing Checklist

- [ ] Traceroute completes for reachable targets
- [ ] HTTP checks return correct status codes
- [ ] HTTPS SSL validation works properly
- [ ] Bandwidth tests measure correctly
- [ ] History endpoints return sorted results
- [ ] Database queries perform efficiently
- [ ] Error messages are helpful and clear
- [ ] Timeouts work without hanging
- [ ] Integration tests pass

---

## 📞 Support & Troubleshooting

### Common Issues

1. **Traceroute hangs / times out**
   - Check network connectivity
   - Verify traceroute command available (`which traceroute`)
   - Increase timeout if testing distant targets

2. **HTTP checks fail with SSL errors**
   - Verify SSL certificate is valid
   - Check certificate expiry
   - Try without HTTPS flag first

3. **Bandwidth tests show slow speeds**
   - Check available bandwidth
   - Verify test server is responsive
   - Run multiple tests to identify patterns

---

**Ready to transform your network monitoring? Start using these diagnostics today!**
