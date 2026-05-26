# NetPulse Session Management Improvements

## Branch: `feature/session-management-improvements`

This branch introduces comprehensive session management, data persistence, and enhanced export functionality to NetPulse. All changes maintain backward compatibility while adding powerful new features.

## 🎯 Key Improvements

### 1. **Session Management System**
- **Create Sessions**: Start tracking each monitoring period as a distinct session
- **Session Metadata**: Add descriptions and notes to sessions
- **View Active Sessions**: See all active, paused, and stopped sessions
- **Session Statistics**: Get aggregated metrics for each session
- **Session Control**: Delete sessions and their associated data
- **Session Filtering**: Filter sessions by target, status, or date range

### 2. **Data Persistence**
- **LocalStorage Integration**: Browser remembers your active target and sessions
- **Auto-save**: Chart data is automatically saved to local storage
- **Refresh Recovery**: No more data loss on page refresh
- **Automatic Cleanup**: Prevents storage overflow by limiting sample history

### 3. **DNS Resolution Lookup**
- **Domain to IP Mapping**: See which IP address a domain resolves to
- **Multiple IP Detection**: Shows all resolved IPs if domain has multiple records
- **Auto-Resolution**: Automatically resolves DNS when adding targets or switching sessions
- **Manual Lookup**: Click "🔍 DNS" button to resolve any target
- **Visual Display**: Primary IP highlighted in cyan with all alternatives listed
- **Error Handling**: Clear messages for NXDOMAIN, missing A records, or DNS failures

### 4. **Enhanced UI/UX**
- **Responsive Layout**: Three-column layout with sessions sidebar
- **Session Panel**: Dedicated left sidebar showing all sessions
- **Status Indicators**: Visual status badges (active/paused/stopped)
- **Session Details**: Expandable session cards showing statistics
- **Session Selector**: Dropdown to quickly switch between sessions
- **Improved Controls**: Better organized monitoring controls
- **DNS Info Card**: Displays resolved IP information with resolver type

### 5. **Advanced Export Features**
- **Multi-format Export**: Export as CSV (spreadsheet) or JSON (data integration)
- **Session-specific Export**: Select which session to export
- **Export Dialog**: Dedicated interface for export configuration
- **Data Integrity**: Includes all metrics and timestamps
- **Batch Operations**: Export multiple sessions

### 6. **Session Statistics**
- **Duration Tracking**: See how long each session ran
- **Aggregated Metrics**: Average, min, max latency and packet loss
- **Record Count**: Total number of metrics collected
- **Session Timeline**: See start, stop, and pause times
- **Performance Insights**: Quick stats without loading raw data

## 📋 Implementation Details

### Database Schema Changes

**New `monitoring_sessions` Table:**
```sql
- session_id: Unique UUID per session
- target: IP/domain being monitored
- status: active, paused, or stopped
- started_at: Session start timestamp
- stopped_at: Session stop timestamp
- paused_at: When session was paused
- resumed_at: When session was resumed
- description: User-provided description
- notes: Additional notes
- created_at: Session creation time
```

**Enhanced `telemetry_metrics` Table:**
- Added `session_id` foreign key to link metrics to sessions
- Added indexes for performance optimization
- Cascade delete support (deleting session removes its metrics)

### API Endpoints

#### DNS Resolution
- `GET /resolve/{target}` - Resolve domain name to IP address(es)
  - Returns primary IP and list of all resolved IPs
  - Handles both IP addresses (validation) and domains (DNS lookup)
  - Error handling for NXDOMAIN, missing A records, DNS failures

#### Session Management
- `POST /sessions` - Create new session
- `GET /sessions` - List all sessions (with filtering)
- `GET /sessions/{id}` - Get specific session
- `PUT /sessions/{id}` - Update session metadata/status
- `DELETE /sessions/{id}` - Delete session and metrics

#### Session Analytics
- `GET /sessions/{id}/stats` - Get session statistics and metrics
- `GET /sessions/{id}/export` - Export session data (CSV/JSON)

### Frontend Components

**New Components:**

1. **SessionPanel.jsx**
   - Displays list of active sessions
   - Session selection and switching
   - Session expansion to view details
   - Quick statistics display
   - Export and delete buttons

2. **SessionDialog.jsx**
   - Modal for creating new sessions
   - Add descriptions and notes
   - Form validation
   - Error handling

3. **ExportDialog.jsx**
   - Select session for export
   - Choose export format (CSV/JSON)
   - Download management

**Utilities:**

1. **storage.js**
   - LocalStorage wrapper functions
   - Session persistence helpers
   - Storage quota monitoring
   - Format utilities (duration, etc.)

**Enhanced App.jsx:**
- Integrated session management
- Data persistence on mount/unmount
- Automatic session polling
- Monitoring state management
- Dialog integration
- Improved error handling

## 🚀 Usage Guide

### Creating a Monitoring Session

1. Add a target (IP or domain)
2. Click "+ Session" to create a new monitoring session
3. Optionally add description and notes
4. The session is automatically set as active

### Starting Monitoring

1. Select a session from the dropdown or session panel
2. Click "▶ Start" to begin monitoring
3. View real-time metrics in the chart
4. Click "⏹ Stop" when done

### Managing Sessions

1. View all sessions in the left panel
2. Click on a session to select it
3. Click "▼" to expand and see statistics
4. Click "Export CSV/JSON" to download data
5. Click "Delete" to remove session

### Switching Between Sessions

- Click on any session in the left panel to switch
- Use the session dropdown in the controls section
- Previous session data is preserved

### Exporting Data

1. Click "📥 Export" button
2. Select the session to export
3. Choose format (CSV for Excel, JSON for data integration)
4. File downloads automatically

## 💾 Data Persistence

**Automatically Saved:**
- Active target IP/domain
- Current session ID
- Recent sessions list
- Chart samples (last 100 points)
- Target history

**Benefits:**
- Survives page refresh
- Survives browser restart
- No data loss
- Auto-recovery on page load

## 🔧 Configuration

### Environment Variables
No new environment variables needed. Existing configuration is used:
- `VITE_API_BASE_URL` - API endpoint
- Database configuration via docker-compose.yml

### Storage Limits
- Session samples limited to 100 points (prevents storage bloat)
- Sessions stored in localStorage
- Automatic cleanup on overflow

## 📊 Performance Improvements

- **Indexed Database Queries**: Fast session and metric lookups
- **Pagination-Ready**: UI supports large session lists
- **Async Operations**: Non-blocking API calls
- **Debounced Refreshes**: 10-second refresh interval
- **Smart Polling**: Only fetches when monitoring is active

## 🔄 Backward Compatibility

All existing functionality is preserved:
- Old export endpoint still works
- Target management unchanged
- Monitoring start/stop works as before
- Existing API endpoints remain
- No breaking changes

## 🐛 Bug Fixes

1. **Data Loss on Refresh**: Fixed with localStorage persistence
2. **No Session Tracking**: Added comprehensive session table
3. **Limited Export**: Enhanced with multi-format support
4. **No Session Control**: Added delete and update operations
5. **No Session Stats**: Added aggregation endpoints

## 🎨 UI/UX Improvements

- Better visual hierarchy
- Responsive design (mobile-friendly)
- Status indicators for sessions
- Collapsible session details
- Organized control panel
- Modal dialogs for actions
- Color-coded status badges

## 📈 Future Enhancements

Possible future additions:
- Session pause/resume in UI
- Scheduled monitoring
- Alert thresholds and notifications
- Metric aggregation over time periods
- Session comparison (A/B testing)
- Custom metric dashboards
- API key management
- User authentication
- Session sharing
- Webhook integrations

## ✅ Testing Checklist

- [ ] Create session works
- [ ] Session persists on page refresh
- [ ] Data persists after browser restart
- [ ] Export CSV format works
- [ ] Export JSON format works
- [ ] Session delete removes data
- [ ] Session statistics accurate
- [ ] Monitoring start/stop works
- [ ] Session switching works
- [ ] Error messages display correctly
- [ ] UI responsive on mobile
- [ ] localStorage doesn't exceed quota

## 📝 Notes

- All database changes are backward compatible
- Existing data is unaffected
- Sessions can be created retroactively for old data
- No migration needed for existing installations
- Full session support from first use

## 🔗 Related Files

- **Backend**: [api-service/app/main.py](../../api-service/app/main.py)
- **Database**: [postgres/init.sql](../../postgres/init.sql)
- **Frontend App**: [frontend/src/App.jsx](../../frontend/src/App.jsx)
- **Components**: [frontend/src/components/](../../frontend/src/components/)
- **Utils**: [frontend/src/utils/storage.js](../../frontend/src/utils/storage.js)

## 🎓 Architecture Overview

```
┌─────────────────────────────────────────┐
│         Browser (React)                 │
│  ┌─────────────────────────────────────┐│
│  │    App.jsx (Main Component)         ││
│  │  - Session Management               ││
│  │  - Monitoring Control               ││
│  │  - Chart Display                    ││
│  └──────────┬──────────────────────────┘│
│             │                            │
│  ┌──────────┴─────────────────────────┐ │
│  │    Sub Components                  │ │
│  │  - SessionPanel.jsx                │ │
│  │  - SessionDialog.jsx               │ │
│  │  - ExportDialog.jsx                │ │
│  └──────────┬──────────────────────────┘ │
│             │                            │
│  ┌──────────┴─────────────────────────┐ │
│  │    Utilities                       │ │
│  │  - storage.js (localStorage)       │ │
│  │  - sessionUtils.js (helpers)       │ │
│  └──────────────────────────────────────┘│
│                                          │
│         localStorage (Browser)           │
│  - Active Target                         │
│  - Active Session ID                     │
│  - Chart Samples                         │
└─────────────────────┬──────────────────────┘
                      │ (API Calls)
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼──────┐          ┌────────▼─────┐
   │  API Service       │  Collector      │
   │  (FastAPI)        │  (Monitoring)   │
   │                    │                 │
   │  New Endpoints:   │ Existing:      │
   │  - /sessions      │ - start        │
   │  - /sessions/{id} │ - stop         │
   │  - /sessions/..../stats          │
   │  - /sessions/..../export         │
   │                    │                 │
   └────┬──────────────┘ └────┬──────────┘
        │                      │
   ┌────▼──────────────────────▼─────┐
   │      PostgreSQL Database        │
   │  - monitoring_sessions (NEW)    │
   │  - telemetry_metrics            │
   │  - Enhanced with session_id FK  │
   └────────────────────────────────┘
```
