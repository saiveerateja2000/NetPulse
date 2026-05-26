import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`

export default function ExportDialog({ isOpen, onClose, sessions, activeSessionId }) {
  const [selectedSessionId, setSelectedSessionId] = useState(activeSessionId || '')
  const [format, setFormat] = useState('csv')

  const handleExport = () => {
    if (!selectedSessionId) return

    const exportUrl = `${API_BASE}/sessions/${selectedSessionId}/export?format=${format}`
    window.location.href = exportUrl
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">Export Session Data</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-300 mb-2">Select Session</label>
            <select
              value={selectedSessionId}
              onChange={(e) => setSelectedSessionId(e.target.value)}
              className="w-full rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            >
              <option value="">-- Choose a session --</option>
              {sessions.map((session) => (
                <option key={session.session_id} value={session.session_id}>
                  {session.target} - {new Date(session.started_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Export Format</label>
            <div className="space-y-2">
              {['csv', 'json'].map((fmt) => (
                <label key={fmt} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value={fmt}
                    checked={format === fmt}
                    onChange={(e) => setFormat(e.target.value)}
                    className="rounded"
                  />
                  <span className="text-sm">
                    {fmt.toUpperCase()}
                    {fmt === 'csv' && ' (Spreadsheet compatible)'}
                    {fmt === 'json' && ' (Machine readable)'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-slate-800 rounded p-3 text-xs text-slate-300">
            <p className="font-semibold mb-1">Export includes:</p>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li>All metrics from the session</li>
              <li>Timestamps for each data point</li>
              <li>Network and system statistics</li>
            </ul>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              onClick={onClose}
              className="flex-1 rounded bg-slate-700 hover:bg-slate-600 px-3 py-2 text-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={!selectedSessionId}
              className="flex-1 rounded bg-violet-600 hover:bg-violet-700 px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Export
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
