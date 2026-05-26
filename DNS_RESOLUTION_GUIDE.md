# 🔍 DNS Resolution Feature Guide

## What's New?

Your NetPulse application now has **DNS resolution functionality** that shows you exactly which IP address a domain name is hitting!

---

## 🎯 What It Does

### Automatic DNS Resolution
- When you **add a new target** (domain), it automatically resolves the domain to its IP address
- When you **switch to a session**, it automatically shows the IP that domain resolves to

### Manual DNS Lookup
- Click the **"🔍 DNS"** button anytime to manually resolve any target
- Works for both IP addresses (validates them) and domain names

### Multi-IP Detection
- If a domain resolves to **multiple IP addresses**, you'll see them all
- The **primary IP** (first one) is highlighted in cyan
- Shows count of total resolved IPs

---

## 📍 How to Use

### **Adding a Domain Target**

```
1. Type a domain name in the Target field
   Example: google.com, cloudflare.com, github.com

2. Click "Add Target"

3. The DNS resolution happens automatically
   You'll see a cyan box showing:
   - Query: google.com
   - Primary IP: 142.250.185.46 (highlighted in cyan)
   - All IPs: (shown if multiple)
```

### **Manual DNS Lookup**

```
1. Select a target (IP or domain)

2. Click the "🔍 DNS" button (loading shows as 🔍...)

3. View the DNS info card showing:
   - Original query
   - Primary IP (cyan highlight)
   - Resolver type (nslookup or ip_validation)
   - All resolved IPs if multiple
```

### **Switching Sessions**

```
1. Click on a session in the left panel

2. DNS is automatically resolved for that session's target

3. See which IP that domain is resolving to
```

---

## 📊 DNS Info Card Display

When DNS resolution succeeds, you'll see:

```
┌─ DNS Resolution ─────────────────────┐
│  Query              google.com        │
│  Primary IP         142.250.185.46    │ ← Highlighted in cyan
│                                       │
│  All IPs (1)                          │
│  → 142.250.185.46                     │
└───────────────────────────────────────┘
```

For domains with **multiple IPs**:

```
┌─ DNS Resolution ─────────────────────┐
│  Query              cloudflare.com    │
│  Primary IP         104.16.132.229    │ ← Highlighted
│                                       │
│  All IPs (2)                          │
│  → 104.16.132.229                     │ ← Primary
│    104.16.133.229                     │
└───────────────────────────────────────┘
```

---

## 🛠️ Technical Details

### Backend Endpoint

```
GET /resolve/{target}
```

**Response Example:**

```json
{
  "query": "google.com",
  "is_ip": false,
  "resolved_ips": ["142.250.185.46"],
  "primary_ip": "142.250.185.46",
  "resolver_used": "nslookup",
  "query_time": "2026-05-26T10:30:45.123Z"
}
```

### Features

- ✅ Domain resolution using nslookup
- ✅ IP address validation
- ✅ Multiple IP detection
- ✅ Error handling:
  - Domain not found (NXDOMAIN)
  - No A records found
  - DNS server errors
- ✅ Comprehensive logging
- ✅ Fast resolution (cached by browser)

---

## 🔧 API Usage

### Resolve a Domain

```bash
curl http://localhost:8000/resolve/google.com
```

**Response:**
```json
{
  "query": "google.com",
  "is_ip": false,
  "resolved_ips": ["142.250.185.46"],
  "primary_ip": "142.250.185.46",
  "resolver_used": "nslookup",
  "query_time": "2026-05-26T10:30:45.123Z"
}
```

### Validate an IP

```bash
curl http://localhost:8000/resolve/8.8.8.8
```

**Response:**
```json
{
  "query": "8.8.8.8",
  "is_ip": true,
  "resolved_ips": ["8.8.8.8"],
  "primary_ip": "8.8.8.8",
  "resolver_used": "ip_validation",
  "query_time": "2026-05-26T10:30:45.123Z"
}
```

---

## 💡 Use Cases

### **1. Verify Target Before Monitoring**
- Add a domain
- See which IP it resolves to
- Confirm it's the right server
- Then start monitoring

### **2. Detect DNS Changes**
- Monitor how DNS resolves over time
- Spot CDN routing changes
- Detect failover events
- Track load balancer changes

### **3. Multi-IP Domains**
- See all IPs for load-balanced domains
- Identify primary server
- Understand distribution

### **4. Troubleshooting**
- Check if domain resolves correctly
- Verify DNS is working
- Identify NXDOMAIN issues
- Confirm A records exist

### **5. Network Analysis**
- Compare which IPs you're reaching
- Identify geographic routing (CDN)
- Detect DNS configuration issues
- Validate infrastructure setup

---

## ⚠️ Error Handling

### **Domain Not Found (NXDOMAIN)**
```
Error: Domain 'invalid-domain-12345.com' not found (NXDOMAIN)
```
- The domain doesn't exist
- Check spelling
- Verify domain is registered

### **No A Records**
```
Error: No A records found for 'example.com'
```
- Domain exists but has no IPv4 records
- May have only IPv6 (AAAA) records
- Configuration issue

### **DNS Server Error**
```
Error: DNS resolution failed: [error details]
```
- DNS server unreachable
- Network connectivity issue
- Check DNS configuration

---

## 🔄 Auto-Resolution Timing

The DNS resolution happens automatically at these times:

1. **Adding a Target** - Resolved immediately after add
2. **Switching Sessions** - Resolved when session selected
3. **Manual Button Click** - Resolved when you click "🔍 DNS"

No need to resolve manually unless you want fresh data.

---

## 📱 Mobile Support

The DNS info card is fully responsive:

- **Desktop**: Full info display with grid layout
- **Tablet**: Stacked layout, readable on smaller screens
- **Mobile**: Compact display, all info visible

Click the "🔍 DNS" button on any device to resolve.

---

## 🎓 Workflow Example

### **Daily Network Monitoring Setup**

```
1. Add target: api.example.com
   → Auto-resolves to 192.168.1.100
   
2. See the IP matches your expected server
   
3. Create session "Daily-API-Check"
   → Session remembers the target
   
4. Click "▶ Start" to monitor
   → Already know which IP we're monitoring
   
5. When done, "📥 Export" the session data
   → Export includes the target and IP we monitored
```

### **Troubleshooting CDN Issues**

```
1. Add target: cdn.example.com
   → Shows: 104.16.132.1
   
2. Wait 5 minutes, click "🔍 DNS" again
   → Shows: 104.16.133.1 (different!)
   
3. Indicates CDN routing changed
   
4. Export data from both IPs for analysis
```

---

## 🚀 Quick Tips

- 🔍 Use DNS lookup to verify targets before monitoring
- 📋 Export session data includes the target IP being monitored
- 🔄 DNS auto-updates when switching between sessions
- 📊 Track IP changes over time by comparing exports
- ⚡ Resolution is fast (typically < 100ms)
- 🌍 Works with any domain globally

---

## 📞 Need Help?

Check the main [IMPROVEMENTS.md](IMPROVEMENTS.md) for:
- Complete API documentation
- Session management features
- Export options

Or see [SESSION_MANAGEMENT_GUIDE.md](SESSION_MANAGEMENT_GUIDE.md) for:
- Step-by-step usage guide
- Common workflows
- Troubleshooting tips

---

**Feature Status:** ✅ Ready to Use

Enjoy DNS resolution! 🎉
