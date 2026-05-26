import { useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || `${window.location.protocol}//${window.location.hostname}:8000`

export default function SessionDialog({ isOpen, onClose, target, onSessionCreated }) {
  const [description, setDescription] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCreateSession = async () => {
    if (!target) {
      setError('Please select a target first')
      return
    }

    try {
      setLoading(true)
      setError('')
      const { data } = await axios.post(`${API_BASE}/sessions`, {
        target,
        description: description || undefined,
        notes: notes || undefined,
      })
      setDescription('')
      setNotes('')
      onSessionCreated(data)
      onClose()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to create session')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-semibold mb-4">Create New Session</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-300 mb-2">Target</label>
            <input
              type="text"
              disabled
              value={target}
              className="w-full rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Morning monitoring session"
              className="w-full rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-2">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any notes about this session..."
              className="w-full rounded bg-slate-800 px-3 py-2 text-sm outline-none ring-1 ring-slate-700 focus:ring-blue-500 h-24 resize-none"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex gap-2 pt-4">
            <button
              onClick={onClose}
              className="flex-1 rounded bg-slate-700 hover:bg-slate-600 px-3 py-2 text-sm"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              onClick={handleCreateSession}
              disabled={loading}
              className="flex-1 rounded bg-blue-600 hover:bg-blue-700 px-3 py-2 text-sm disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Session'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
