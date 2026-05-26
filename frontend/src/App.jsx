import { useMemo, useState, useEffect } from 'react'
import axios from 'axios'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'
import SessionPanel from './components/SessionPanel'
import SessionDialog from './components/SessionDialog'
import ExportDialog from './components/ExportDialog'
import { storage, sessionUtils } from './utils/storage'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`

function App() {
  // Core monitoring state
  const [target, setTarget] = useState(() => storage.getActiveTarget())
  const [activeTarget, setActiveTarget] = useState(() => storage.getActiveTarget())
  const [status, setStatus] = useState('idle')
  const [samples, setSamples] = useState(() => storage.getSamples())
  const [error, setError] = useState('')

  // Session management state
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(() => storage.getActiveSession())
  const [sessionDialogOpen, setSessionDialogOpen] = useState(false)
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [allTargets, setAllTargets] = useState(() => storage.getTargets())

  // Monitor/polling state
  const [monitoringInterval, setMonitoringInterval] = useState(null)
  const [isMonitoring, setIsMonitoring] = useState(false)

  // DNS resolution state
  const [dnsInfo, setDnsInfo] = useState(null)
  const [dnsLoading, setDnsLoading] = useState(false)

  const latest = useMemo(() => (samples.length ? samples[samples.length - 1] : null), [samples])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
    const interval = setInterval(loadSessions, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  // Auto-save samples to localStorage
  useEffect(() => {
    storage.setSamples(samples)
  }, [samples])

  // Load all sessions from API
  const loadSessions = async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/sessions`)
      setSessions(data)
      storage.setRecentSessions(data)
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  // Add target
  const addTarget = async () => {
    setError('')
    setStatus(`Adding target ${target}...`)
    try {
      await axios.post(`${API_BASE}/targets`, { target })
      setStatus(`✓ Target ${target} added`)
      setActiveTarget(target)
      setAllTargets((prev) => [...new Set([...prev, target])])
      storage.setActiveTarget(target)
      storage.setTargets([...new Set([...allTargets, target])])
      // Resolve DNS for newly added target
      resolveDNS(target)
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to add target'
      setError(errorMsg)
      setStatus('idle')
      console.error('Add target error:', e)
    }
  }

  // Resolve DNS
  const resolveDNS = async (targetToResolve = activeTarget) => {
    if (!targetToResolve) {
      setError('Please select a target first')
      return
    }
    
    try {
      setDnsLoading(true)
      setError('')
      const { data } = await axios.get(`${API_BASE}/resolve/${encodeURIComponent(targetToResolve)}`)
      setDnsInfo(data)
      setStatus(`✓ Resolved ${targetToResolve} to ${data.primary_ip}`)
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to resolve DNS'
      setError(errorMsg)
      setDnsInfo(null)
      console.error('DNS resolution error:', e)
    } finally {
      setDnsLoading(false)
    }
  }

  // Create session
  const createSession = async () => {
    if (!activeTarget) {
      setError('Please select a target first')
      return
    }
    setSessionDialogOpen(true)
  }

  const handleSessionCreated = async (newSession) => {
    setActiveSessionId(newSession.session_id)
    storage.setActiveSession(newSession.session_id)
    setSamples([]) // Clear samples for new session
    setStatus(`✓ Session created for ${newSession.target}`)
    await loadSessions()
  }

  // Start monitoring
  const start = async () => {
    setError('')
    
    if (!activeSessionId) {
      setError('Create a session first')
      return
    }

    setStatus(`Starting monitoring for ${activeTarget}...`)
    try {
      const response = await axios.post(`${API_BASE}/monitoring/start`, { target: activeTarget })
      setStatus(`✓ Monitoring started for ${activeTarget}`)
      setSamples([]) // Clear old samples
      setIsMonitoring(true)

      // Start polling for live metrics
      if (monitoringInterval) clearInterval(monitoringInterval)
      const interval = setInterval(fetchLive, 2000)
      setMonitoringInterval(interval)
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to start monitoring'
      setError(errorMsg)
      setStatus('idle')
      setIsMonitoring(false)
      console.error('Start monitoring error:', e)
    }
  }

  // Stop monitoring
  const stop = async () => {
    setError('')
    setStatus(`Stopping monitoring for ${activeTarget}...`)
    try {
      await axios.post(`${API_BASE}/monitoring/stop`, { target: activeTarget })
      setStatus(`✓ Monitoring stopped for ${activeTarget}`)
      setSamples([])
      setIsMonitoring(false)
      if (monitoringInterval) {
        clearInterval(monitoringInterval)
        setMonitoringInterval(null)
      }
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to stop monitoring'
      setError(errorMsg)
      setStatus('idle')
      console.error('Stop monitoring error:', e)
    }
  }

  // Fetch live metrics
  const fetchLive = async () => {
    if (!activeTarget) {
      setError('Please select a target first')
      return
    }
    try {
      const { data } = await axios.get(`${API_BASE}/metrics/live/${activeTarget}`)
      const point = {
        time: new Date(data.timestamp).toLocaleTimeString(),
        latency_ms: data.latency_ms,
        packet_loss: data.packet_loss,
        jitter: data.jitter,
      }
      setSamples((prev) => [...prev.slice(-29), point])
      setError('')
    } catch (e) {
      if (e?.response?.status !== 404) {
        const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to fetch metrics'
        setError(errorMsg)
        console.error('Fetch live metrics error:', e)
      }
    }
  }

  // Fetch events
  const fetchEvents = async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/stream/events`)
      setStatus(`✓ Kafka stream topic: ${data.topic} (${data.sessions.length} active sessions)`)
      setError('')
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to fetch stream events'
      setError(errorMsg)
      console.error('Fetch events error:', e)
    }
  }

  // Select session
  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId)
    storage.setActiveSession(sessionId)
    const session = sessions.find((s) => s.session_id === sessionId)
    if (session) {
      setActiveTarget(session.target)
      setTarget(session.target)
      storage.setActiveTarget(session.target)
      setSamples([]) // Clear samples when switching sessions
      resolveDNS(session.target) // Resolve DNS for the selected session's target
    }
  }

  // Delete session
  const handleDeleteSession = (sessionId) => {
    setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
    if (activeSessionId === sessionId) {
      setActiveSessionId(null)
      storage.clearActiveSession()
      setSamples([])
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            NetPulse
          </h1>
          <p className="text-sm text-slate-400 mt-2">Real-time network telemetry with session management</p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Sessions */}
          <div className="lg:col-span-1">
            <SessionPanel
              sessions={sessions}
              onSessionSelect={handleSelectSession}
              onSessionDelete={handleDeleteSession}
              onSessionRefresh={loadSessions}
              activeSessionId={activeSessionId}
            />
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Target & Monitoring Controls */}
            <div className="rounded-lg border border-slate-700 bg-slate-900 p-4 space-y-3">
              <h2 className="font-semibold">Monitoring Controls</h2>
              <div className="space-y-3">
                {/* Target Selection */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Target (IP or Domain)</label>
                  <div className="flex gap-2">
                    <input
                      className="flex-1 rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 focus:ring-blue-500"
                      value={target}
                      onChange={(e) => setTarget(e.target.value)}
                      placeholder="8.8.8.8 or google.com"
                    />
                    <button className="rounded bg-blue-600 hover:bg-blue-700 px-4 py-2 text-sm" onClick={addTarget}>
                      Add Target
                    </button>
                    <button
                      className="rounded bg-cyan-600 hover:bg-cyan-700 px-4 py-2 text-sm disabled:opacity-50"
                      onClick={() => resolveDNS()}
                      disabled={!activeTarget || dnsLoading}
                    >
                      {dnsLoading ? '🔍...' : '🔍 DNS'}
                    </button>
                  </div>
                </div>

                {/* DNS Resolution Info */}
                {dnsInfo && (
                  <div className="rounded-lg bg-slate-800/50 border border-cyan-700/50 p-3 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-400 font-semibold">DNS Resolution</span>
                      <span className="text-xs text-cyan-400">{dnsInfo.resolver_used}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <p className="text-xs text-slate-500">Query</p>
                        <p className="text-sm font-mono text-slate-200">{dnsInfo.query}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Primary IP</p>
                        <p className="text-sm font-mono text-cyan-400 font-semibold">{dnsInfo.primary_ip}</p>
                      </div>
                    </div>
                    {dnsInfo.resolved_ips.length > 1 && (
                      <div>
                        <p className="text-xs text-slate-500">All IPs ({dnsInfo.resolved_ips.length})</p>
                        <div className="text-xs font-mono text-slate-300 space-y-1">
                          {dnsInfo.resolved_ips.map((ip, idx) => (
                            <div key={idx} className={idx === 0 ? 'text-cyan-400 font-semibold' : ''}>
                              {idx === 0 ? '→ ' : '  '} {ip}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Session Management */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Active Session</label>
                  <div className="flex gap-2">
                    <select
                      value={activeSessionId || ''}
                      onChange={(e) => handleSelectSession(e.target.value)}
                      className="flex-1 rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 focus:ring-blue-500"
                    >
                      <option value="">-- Select Session or Create New --</option>
                      {sessions.map((s) => (
                        <option key={s.session_id} value={s.session_id}>
                          {s.target} ({s.status}) - {new Date(s.started_at).toLocaleString()}
                        </option>
                      ))}
                    </select>
                    <button
                      className="rounded bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm"
                      onClick={createSession}
                    >
                      + Session
                    </button>
                  </div>
                </div>

                {/* Control Buttons */}
                <div className="flex flex-wrap gap-2">
                  <button
                    className="rounded bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm disabled:opacity-50"
                    onClick={start}
                    disabled={!activeTarget || !activeSessionId}
                  >
                    ▶ Start
                  </button>
                  <button
                    className="rounded bg-rose-600 hover:bg-rose-700 px-4 py-2 text-sm disabled:opacity-50"
                    onClick={stop}
                    disabled={!isMonitoring}
                  >
                    ⏹ Stop
                  </button>
                  <button className="rounded bg-slate-700 hover:bg-slate-600 px-4 py-2 text-sm" onClick={fetchLive}>
                    🔄 Refresh
                  </button>
                  <button className="rounded bg-slate-700 hover:bg-slate-600 px-4 py-2 text-sm" onClick={fetchEvents}>
                    📡 Kafka
                  </button>
                  <button
                    className="rounded bg-violet-700 hover:bg-violet-800 px-4 py-2 text-sm disabled:opacity-50"
                    onClick={() => setExportDialogOpen(true)}
                    disabled={sessions.length === 0}
                  >
                    📥 Export
                  </button>
                </div>

                {/* Status */}
                <div className="text-xs text-slate-400">
                  {error ? (
                    <span className="text-red-400">Error: {error}</span>
                  ) : (
                    <span>
                      Status: {status} {isMonitoring && <span className="animate-pulse">● monitoring</span>}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Metrics Cards */}
            <div className="grid gap-4 md:grid-cols-3">
              <MetricCard title="Latency" value={latest ? `${latest.latency_ms} ms` : '--'} />
              <MetricCard title="Packet Loss" value={latest ? `${latest.packet_loss}%` : '--'} />
              <MetricCard title="Jitter" value={latest ? `${latest.jitter} ms` : '--'} />
            </div>

            {/* Chart */}
            <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
              <h2 className="mb-3 font-semibold">Real-Time Metrics</h2>
              {samples.length === 0 ? (
                <div className="h-72 flex items-center justify-center text-slate-400">
                  Start monitoring to see real-time data
                </div>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer>
                    <LineChart data={samples}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="time" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip />
                      <Line type="monotone" dataKey="latency_ms" stroke="#38bdf8" dot={false} />
                      <Line type="monotone" dataKey="packet_loss" stroke="#f43f5e" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <SessionDialog
        isOpen={sessionDialogOpen}
        onClose={() => setSessionDialogOpen(false)}
        target={activeTarget}
        onSessionCreated={handleSessionCreated}
      />

      <ExportDialog
        isOpen={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        sessions={sessions}
        activeSessionId={activeSessionId}
      />
    </div>
  )
}

function MetricCard({ title, value }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <h3 className="text-sm text-slate-400">{title}</h3>
      <p className="mt-2 text-2xl font-bold">{value}</p>
    </div>
  )
}

export default App
