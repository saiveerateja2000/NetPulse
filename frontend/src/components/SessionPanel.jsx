import { useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`

export default function SessionPanel({ sessions, onSessionSelect, onSessionDelete, onSessionRefresh, activeSessionId }) {
  const [expandedSessions, setExpandedSessions] = useState(new Set())
  const [loadingStats, setLoadingStats] = useState({})
  const [sessionStats, setSessionStats] = useState({})

  const toggleExpanded = (sessionId) => {
    const newExpanded = new Set(expandedSessions)
    if (newExpanded.has(sessionId)) {
      newExpanded.delete(sessionId)
    } else {
      newExpanded.add(sessionId)
      loadStats(sessionId)
    }
    setExpandedSessions(newExpanded)
  }

  const loadStats = async (sessionId) => {
    try {
      setLoadingStats((prev) => ({ ...prev, [sessionId]: true }))
      const { data } = await axios.get(`${API_BASE}/sessions/${sessionId}/stats`)
      setSessionStats((prev) => ({ ...prev, [sessionId]: data }))
    } catch (error) {
      console.error('Failed to load session stats:', error)
    } finally {
      setLoadingStats((prev) => ({ ...prev, [sessionId]: false }))
    }
  }

  const handleDelete = async (sessionId) => {
    if (window.confirm('Are you sure you want to delete this session and all its data?')) {
      try {
        await axios.delete(`${API_BASE}/sessions/${sessionId}`)
        onSessionDelete(sessionId)
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
  }

  const handleExport = (sessionId, format = 'csv') => {
    window.location.href = `${API_BASE}/sessions/${sessionId}/export?format=${format}`
  }

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-900/50 text-green-300'
      case 'paused':
        return 'bg-yellow-900/50 text-yellow-300'
      case 'stopped':
        return 'bg-red-900/50 text-red-300'
      default:
        return 'bg-slate-700'
    }
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <h2 className="mb-4 font-semibold text-lg">Active Sessions ({sessions.length})</h2>

      {sessions.length === 0 ? (
        <p className="text-sm text-slate-400">No sessions yet. Add a target and start monitoring.</p>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className={`rounded-lg border p-3 cursor-pointer transition ${
                activeSessionId === session.session_id
                  ? 'border-blue-500 bg-blue-900/30'
                  : 'border-slate-700 bg-slate-800/50 hover:bg-slate-800'
              }`}
              onClick={() => onSessionSelect(session.session_id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{session.target}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getStatusColor(session.status)}`}>
                      {session.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Started: {new Date(session.started_at).toLocaleString()}
                  </p>
                  {session.description && <p className="text-xs text-slate-300 mt-1">{session.description}</p>}
                </div>
                <button
                  className="ml-2 text-slate-400 hover:text-slate-200 text-xl leading-none"
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleExpanded(session.session_id)
                  }}
                >
                  {expandedSessions.has(session.session_id) ? '▼' : '▶'}
                </button>
              </div>

              {expandedSessions.has(session.session_id) && (
                <div className="mt-3 border-t border-slate-700 pt-3 space-y-2">
                  {loadingStats[session.session_id] ? (
                    <p className="text-xs text-slate-400">Loading stats...</p>
                  ) : sessionStats[session.session_id] ? (
                    <>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <p className="text-slate-400">Duration</p>
                          <p className="font-mono">{formatDuration(sessionStats[session.session_id].duration_seconds)}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Records</p>
                          <p className="font-mono">{sessionStats[session.session_id].metrics.total_records}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Avg Latency</p>
                          <p className="font-mono">
                            {sessionStats[session.session_id].metrics.avg_latency_ms?.toFixed(2) || '-'} ms
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">Avg Loss</p>
                          <p className="font-mono">
                            {sessionStats[session.session_id].metrics.avg_packet_loss?.toFixed(2) || '-'}%
                          </p>
                        </div>
                      </div>

                      <div className="flex gap-2 pt-2">
                        <button
                          className="flex-1 rounded bg-violet-700 hover:bg-violet-600 px-2 py-1 text-xs"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleExport(session.session_id, 'csv')
                          }}
                        >
                          Export CSV
                        </button>
                        <button
                          className="flex-1 rounded bg-slate-700 hover:bg-slate-600 px-2 py-1 text-xs"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleExport(session.session_id, 'json')
                          }}
                        >
                          JSON
                        </button>
                        <button
                          className="flex-1 rounded bg-red-700 hover:bg-red-600 px-2 py-1 text-xs"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(session.session_id)
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <button
        className="mt-4 w-full rounded bg-slate-700 hover:bg-slate-600 px-3 py-2 text-sm"
        onClick={onSessionRefresh}
      >
        Refresh Sessions
      </button>
    </div>
  )
}
