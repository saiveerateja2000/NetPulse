import { useState } from 'react'
import axios from 'axios'
import TracerouteViewer from './diagnostics/TracerouteViewer'
import HTTPCheckViewer from './diagnostics/HTTPCheckViewer'
import BandwidthTestViewer from './diagnostics/BandwidthTestViewer'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`

export default function DiagnosticsPanel({ activeTarget, allTargets }) {
  const [activeTab, setActiveTab] = useState('http-check')
  const [selectedTarget, setSelectedTarget] = useState(activeTarget)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Traceroute state
  const [tracerouteData, setTracerouteData] = useState(null)
  const [tracerouteHistory, setTracerouteHistory] = useState([])

  // HTTP Check state
  const [httpCheckData, setHttpCheckData] = useState(null)
  const [httpCheckHistory, setHttpCheckHistory] = useState([])
  const [useHttps, setUseHttps] = useState(true)

  // Bandwidth Test state
  const [bandwidthData, setBandwidthData] = useState(null)
  const [bandwidthHistory, setBandwidthHistory] = useState([])
  const [testSize, setTestSize] = useState(10)

  const handleError = (msg) => {
    setError(msg)
    setTimeout(() => setError(''), 5000)
  }

  const handleSuccess = (msg) => {
    setSuccess(msg)
    setTimeout(() => setSuccess(''), 3000)
  }

  // Traceroute functions
  const runTraceroute = async () => {
    if (!selectedTarget) {
      handleError('Please select a target')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { data } = await axios.post(`${API_BASE}/diagnostics/traceroute`, {
        target: selectedTarget,
      })
      setTracerouteData(data)
      handleSuccess('Traceroute completed')
      await loadTracerouteHistory()
    } catch (err) {
      handleError(err?.response?.data?.detail || 'Traceroute failed')
    } finally {
      setLoading(false)
    }
  }

  const loadTracerouteHistory = async () => {
    try {
      const { data } = await axios.get(
        `${API_BASE}/diagnostics/traceroute/${selectedTarget}?limit=5`
      )
      setTracerouteHistory(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load traceroute history:', err)
    }
  }

  // HTTP Check functions
  const runHttpCheck = async () => {
    if (!selectedTarget) {
      handleError('Please select a target')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { data } = await axios.post(`${API_BASE}/diagnostics/http-check`, {
        target: selectedTarget,
        use_https: useHttps,
      })
      setHttpCheckData(data)
      handleSuccess('HTTP check completed')
      await loadHttpCheckHistory()
    } catch (err) {
      handleError(err?.response?.data?.detail || 'HTTP check failed')
    } finally {
      setLoading(false)
    }
  }

  const loadHttpCheckHistory = async () => {
    try {
      const { data } = await axios.get(
        `${API_BASE}/diagnostics/http-check/${selectedTarget}?limit=10`
      )
      setHttpCheckHistory(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load HTTP check history:', err)
    }
  }

  // Bandwidth Test functions
  const runBandwidthTest = async () => {
    if (!selectedTarget) {
      handleError('Please select a target')
      return
    }
    setLoading(true)
    setError('')
    try {
      const { data } = await axios.post(`${API_BASE}/diagnostics/bandwidth-test`, {
        target: selectedTarget,
        test_size_mb: testSize,
      })
      setBandwidthData(data)
      handleSuccess('Bandwidth test completed')
      await loadBandwidthHistory()
    } catch (err) {
      handleError(err?.response?.data?.detail || 'Bandwidth test failed')
    } finally {
      setLoading(false)
    }
  }

  const loadBandwidthHistory = async () => {
    try {
      const { data } = await axios.get(
        `${API_BASE}/diagnostics/bandwidth-test/${selectedTarget}?limit=10`
      )
      setBandwidthHistory(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load bandwidth history:', err)
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <h2 className="text-lg font-semibold mb-4">Network Diagnostics</h2>

        {/* Target Selection */}
        <div className="mb-4 flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2 text-slate-300">Target</label>
            <select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-slate-100"
            >
              <option value="">Select a target</option>
              {allTargets.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-600 rounded text-red-300 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-900/50 border border-green-600 rounded text-green-300 text-sm">
            {success}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="rounded-lg border border-slate-700 bg-slate-900 overflow-hidden">
        <div className="flex border-b border-slate-700">
          {[
            { id: 'http-check', label: '📡 HTTP Check', icon: '🌐' },
            { id: 'traceroute', label: '🗺️ Traceroute', icon: '📍' },
            { id: 'bandwidth', label: '⚡ Bandwidth', icon: '📊' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-3 text-center font-medium transition ${
                activeTab === tab.id
                  ? 'bg-slate-800 text-blue-400 border-b-2 border-blue-400'
                  : 'text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-4">
          {activeTab === 'http-check' && (
            <HTTPCheckViewer
              data={httpCheckData}
              history={httpCheckHistory}
              loading={loading}
              onRun={runHttpCheck}
              useHttps={useHttps}
              onHttpsChange={setUseHttps}
              target={selectedTarget}
            />
          )}
          {activeTab === 'traceroute' && (
            <TracerouteViewer
              data={tracerouteData}
              history={tracerouteHistory}
              loading={loading}
              onRun={runTraceroute}
              target={selectedTarget}
            />
          )}
          {activeTab === 'bandwidth' && (
            <BandwidthTestViewer
              data={bandwidthData}
              history={bandwidthHistory}
              loading={loading}
              onRun={runBandwidthTest}
              testSize={testSize}
              onTestSizeChange={setTestSize}
              target={selectedTarget}
            />
          )}
        </div>
      </div>
    </div>
  )
}
