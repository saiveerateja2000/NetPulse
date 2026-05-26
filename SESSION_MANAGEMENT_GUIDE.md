# NetPulse Session Management - Quick Start Guide

## 🚀 Getting Started

### What's New?

Your NetPulse application now has powerful session management features that allow you to:

✅ **Track multiple monitoring sessions** - Each session is a separate monitoring period  
✅ **Persistent data** - Your data survives browser refresh  
✅ **Session statistics** - View aggregated metrics for any session  
✅ **Export flexibility** - Export as CSV or JSON  
✅ **Session control** - Create, manage, and delete sessions  

## 📖 Step-by-Step Usage

### 1. **Add a Target to Monitor**

```
1. In the "Monitoring Controls" section, enter an IP or domain
2. Click "Add Target" button
3. You should see a confirmation message
```

Examples: `8.8.8.8`, `google.com`, `1.1.1.1`

### 2. **Create a New Monitoring Session**

```
1. Click the "+ Session" button
2. (Optional) Add a description like "Morning monitoring"
3. (Optional) Add notes like "Testing network latency"
4. Click "Create Session"
```

Your session is now ready to use and will appear in the left panel.

### 3. **Start Monitoring**

```
1. Make sure your target is selected
2. Make sure your session is selected (shown in dropdown)
3. Click "▶ Start" button
4. Watch the real-time metrics appear in the chart
5. See live values for Latency, Packet Loss, and Jitter
```

### 4. **Stop Monitoring**

```
1. Click "⏹ Stop" button
2. Your data is automatically saved
3. You can switch to another session or continue viewing this data
```

### 5. **View Session Statistics**

In the left **Session Panel**:

```
1. Find your session in the list
2. Click the arrow (▼) to expand it
3. View:
   - Duration (how long it ran)
   - Total Records collected
   - Average Latency
   - Average Packet Loss
```

### 6. **Export Session Data**

**Option A: From Session Panel**
```
1. Expand the session (click ▼)
2. Click "Export CSV" for spreadsheet format
3. Or click "JSON" for machine-readable format
```

**Option B: Using Export Dialog**
```
1. Click "📥 Export" button in controls
2. Select which session to export
3. Choose format (CSV or JSON)
4. Click "Export"
5. File downloads automatically
```

### 7. **Delete a Session**

```
1. In the Session Panel, expand the session
2. Click "Delete" button
3. Confirm the deletion
4. Session and all its data are permanently removed
```

### 8. **Switch Between Sessions**

**Method 1: Session Panel**
```
1. Click on any session in the left panel
2. Charts and metrics update automatically
```

**Method 2: Dropdown**
```
1. Use the "Active Session" dropdown in controls
2. Select the session you want
3. View its data
```

## 💡 Tips & Tricks

### **Data Persistence**
- Your active target is automatically saved
- Your recent sessions are remembered
- Chart data persists even after closing the browser
- Just refresh the page and your data is there!

### **Session Organization**
- Add meaningful descriptions when creating sessions
- Use notes to remember what you were testing
- Group sessions by time period or target

### **Exporting Data**
- **CSV Format**: Best for Excel spreadsheets and analysis
- **JSON Format**: Best for importing into other tools or databases
- Each session has a unique file with timestamp

### **Multiple Targets**
- Add multiple IP addresses or domains
- Switch between them using the dropdown
- Each gets its own monitoring sessions

### **Monitoring Best Practices**
- Create a session before starting to monitor
- Add a description for reference later
- Use consistent naming for similar sessions
- Stop monitoring before switching targets

## 🎯 Common Workflows

### **Daily Network Health Check**

```
1. Create session "Daily-Morning-Check"
2. Monitor google.com for 5 minutes
3. Export CSV and save to your reports folder
4. View the statistics
```

### **Comparing Two Targets**

```
1. Create session "Test-ISP-A"
2. Monitor ISP-A for 5 minutes, export
3. Create session "Test-ISP-B"
4. Monitor ISP-B for 5 minutes, export
5. Compare the CSV files
```

### **Long-term Monitoring**

```
1. Create session "Long-term-monitoring"
2. Keep monitoring running
3. Periodically check statistics using expand button
4. Export data at the end of monitoring period
```

### **Troubleshooting a Problem**

```
1. Create session "Troubleshooting-Session-1"
2. Monitor with detailed description of the issue
3. Export data with full timestamps
4. Share with network team for analysis
```

## ⚙️ Configuration

### **Storage**
- Browser stores up to 100 recent chart samples
- Prevents storage overflow
- Automatically cleaned up

### **Refresh Rate**
- Sessions list refreshes every 10 seconds
- Live metrics refresh every 2 seconds while monitoring
- Automatic debouncing prevents excessive API calls

### **Export Formats**

**CSV (Spreadsheet Compatible)**
```
Columns: target, latency_ms, packet_loss, jitter, dns_lookup_time,
         cpu_usage, memory_usage, bandwidth_usage, active_connections,
         traceroute_hops, timestamp
```

**JSON (Machine Readable)**
```json
[
  {
    "target": "8.8.8.8",
    "latency_ms": 25.5,
    "packet_loss": 0,
    "jitter": 2.3,
    "dns_lookup_time": 5,
    "cpu_usage": 15.2,
    "memory_usage": 45.3,
    "bandwidth_usage": 1024,
    "active_connections": 42,
    "traceroute_hops": "path_data",
    "timestamp": "2024-05-26T10:30:45.123Z"
  }
]
```

## 🆘 Troubleshooting

### **"Data Lost After Refresh"**
✅ **Fixed!** New feature automatically saves your data
- Your session and chart data persists
- Reload the page - everything should be there
- Check localStorage settings in browser

### **"Can't See Export Options"**
- Make sure you have created at least one session
- Sessions can be empty (no monitoring data yet)
- Export button becomes active when sessions exist

### **"Session List Not Updating"**
- List refreshes every 10 seconds automatically
- Click "Refresh Sessions" to manually update
- Check if monitoring is actually running

### **"Export File Won't Download"**
- Check browser's download settings
- Try a different format (CSV or JSON)
- Check browser console for errors

## 🎨 UI Elements Explained

**Status Colors:**
- 🟢 **Green** - Session is active/monitoring
- 🟡 **Yellow** - Session is paused
- 🔴 **Red** - Session is stopped

**Buttons:**
- `▶ Start` - Begin monitoring
- `⏹ Stop` - Stop monitoring
- `🔄 Refresh` - Get latest metrics
- `📡 Kafka` - Check stream events
- `📥 Export` - Export session data
- `+ Session` - Create new session

**Dropdown Indicators:**
- `▼` - Session panel is expanded, showing details
- `▶` - Session panel is collapsed, click to expand

## 📚 More Information

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for:
- Complete feature list
- API endpoint documentation
- Database schema details
- Architecture overview
- Future enhancement ideas

## ✅ Checklist for First Use

- [ ] Added a target (IP or domain)
- [ ] Created a monitoring session
- [ ] Started monitoring
- [ ] Viewed the real-time chart
- [ ] Stopped monitoring
- [ ] Viewed session statistics
- [ ] Exported data as CSV or JSON
- [ ] Refreshed the page and saw data persist
- [ ] Switched between sessions
- [ ] Deleted a test session

## 🎓 Next Steps

Once comfortable with basic usage:

1. **Create multiple sessions** for different targets
2. **Export and analyze** data in Excel or Python
3. **Monitor long-term** trends by comparing sessions
4. **Set up recurring** monitoring checks
5. **Share data** with team members via exports

---

**Need Help?** Check the [API Documentation](../../api-service/app/main.py) or review [IMPROVEMENTS.md](IMPROVEMENTS.md)
