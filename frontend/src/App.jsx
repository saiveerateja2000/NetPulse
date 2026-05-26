import { useMemo, useState } from 'react'
import axios from 'axios'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  `${window.location.protocol}//${window.location.hostname}:8000`

function App() {
  const [target, setTarget] = useState('8.8.8.8')
  const [activeTarget, setActiveTarget] = useState('8.8.8.8')
  const [status, setStatus] = useState('idle')
  const [samples, setSamples] = useState([])
  const [error, setError] = useState('')

  const latest = useMemo(() => (samples.length ? samples[samples.length - 1] : null), [samples])
  const exportUrl = `${API_BASE}/reports/export/${encodeURIComponent(activeTarget)}`

  const addTarget = async () => {
    setError('')
    setStatus(`Adding target ${target}...`)
    try {
      await axios.post(`${API_BASE}/targets`, { target })
      setStatus(`✓ Target ${target} added`)
      setActiveTarget(target)
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to add target'
      setError(errorMsg)
      setStatus('idle')
      console.error('Add target error:', e)
    }
  }

  const start = async () => {
    setError('')
    setStatus(`Starting monitoring for ${activeTarget}...`)
    try {
      const response = await axios.post(`${API_BASE}/monitoring/start`, { target: activeTarget })
      setStatus(`✓ Monitoring started for ${activeTarget}`)
      // Start polling for live metrics
      const pollInterval = setInterval(fetchLive, 2000)
      return () => clearInterval(pollInterval)
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to start monitoring'
      setError(errorMsg)
      setStatus('idle')
      console.error('Start monitoring error:', e)
    }
  }

  const stop = async () => {
    setError('')
    setStatus(`Stopping monitoring for ${activeTarget}...`)
    try {
      await axios.post(`${API_BASE}/monitoring/stop`, { target: activeTarget })
      setStatus(`✓ Monitoring stopped for ${activeTarget}`)
      setSamples([])
    } catch (e) {
      const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to stop monitoring'
      setError(errorMsg)
      setStatus('idle')
      console.error('Stop monitoring error:', e)
    }
  }

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

  return (
    <div className="min-h-screen p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <h1 className="text-3xl font-bold">NetPulse</h1>
        <p className="text-sm text-slate-300">Real-time lightweight network telemetry and analytics platform</p>

        <div className="rounded-lg border border-slate-700 bg-slate-900 p-4 space-y-3">
          <h2 className="font-semibold">Add Monitoring Target</h2>
          <div className="flex flex-wrap gap-2">
            <input
              className="rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="8.8.8.8 or google.com"
            />
            <button className="rounded bg-blue-600 px-4 py-2 text-sm" onClick={addTarget}>Add Target</button>
            <button className="rounded bg-emerald-600 px-4 py-2 text-sm" onClick={start}>Start Monitoring</button>
            <button className="rounded bg-rose-600 px-4 py-2 text-sm" onClick={stop}>Stop Monitoring</button>
            <button className="rounded bg-slate-700 px-4 py-2 text-sm" onClick={fetchLive}>Live Network Metrics</button>
            <button className="rounded bg-slate-700 px-4 py-2 text-sm" onClick={fetchEvents}>Kafka Stream Events</button>
            <a className="rounded bg-violet-700 px-4 py-2 text-sm" href={exportUrl}>Export Reports</a>
          </div>
          <p className="text-xs text-slate-400">Target Status: {status} {error ? `| Error: ${error}` : ''}</p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard title="Latency" value={latest ? `${latest.latency_ms} ms` : '--'} />
          <MetricCard title="Packet Loss" value={latest ? `${latest.packet_loss}%` : '--'} />
          <MetricCard title="Jitter" value={latest ? `${latest.jitter} ms` : '--'} />
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
          <h2 className="mb-3 font-semibold">Real-Time Charts / Historical Trends</h2>
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
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  )
}

export default App
