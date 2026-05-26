// LocalStorage persistence utilities for NetPulse

const STORAGE_KEYS = {
  ACTIVE_TARGET: 'netpulse_active_target',
  ACTIVE_SESSION: 'netpulse_active_session',
  RECENT_SESSIONS: 'netpulse_recent_sessions',
  TARGETS: 'netpulse_targets',
  SAMPLES: 'netpulse_samples',
}

export const storage = {
  // Active monitoring target
  setActiveTarget(target) {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_TARGET, target)
  },

  getActiveTarget() {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_TARGET) || '8.8.8.8'
  },

  // Active session
  setActiveSession(sessionId) {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, sessionId)
  },

  getActiveSession() {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION)
  },

  clearActiveSession() {
    localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION)
  },

  // Recent sessions list
  setRecentSessions(sessions) {
    localStorage.setItem(STORAGE_KEYS.RECENT_SESSIONS, JSON.stringify(sessions.slice(0, 10)))
  },

  getRecentSessions() {
    const data = localStorage.getItem(STORAGE_KEYS.RECENT_SESSIONS)
    return data ? JSON.parse(data) : []
  },

  // Available targets
  setTargets(targets) {
    localStorage.setItem(STORAGE_KEYS.TARGETS, JSON.stringify(targets))
  },

  getTargets() {
    const data = localStorage.getItem(STORAGE_KEYS.TARGETS)
    return data ? JSON.parse(data) : ['8.8.8.8']
  },

  // Chart samples (limited to prevent storage bloat)
  setSamples(samples) {
    // Keep only last 100 samples to prevent localStorage overflow
    const limitedSamples = samples.slice(-100)
    localStorage.setItem(STORAGE_KEYS.SAMPLES, JSON.stringify(limitedSamples))
  },

  getSamples() {
    const data = localStorage.getItem(STORAGE_KEYS.SAMPLES)
    return data ? JSON.parse(data) : []
  },

  // Clear all data
  clear() {
    Object.values(STORAGE_KEYS).forEach((key) => {
      localStorage.removeItem(key)
    })
  },

  // Get storage usage
  getStorageInfo() {
    const keys = Object.values(STORAGE_KEYS)
    let totalSize = 0

    keys.forEach((key) => {
      const value = localStorage.getItem(key)
      if (value) {
        totalSize += value.length
      }
    })

    return {
      size: totalSize,
      keys: keys.length,
      isFull: totalSize > 1024 * 1024, // 1MB threshold
    }
  },
}

// Session management utilities
export const sessionUtils = {
  // Parse session display info
  formatSessionInfo(session) {
    return {
      id: session.session_id,
      target: session.target,
      status: session.status,
      startTime: new Date(session.started_at),
      isActive: session.status === 'active',
      isPaused: session.status === 'paused',
      isStopped: session.status === 'stopped',
    }
  },

  // Format duration for display
  formatDuration(startTime, endTime = null) {
    const end = endTime ? new Date(endTime) : new Date()
    const start = new Date(startTime)
    const seconds = Math.floor((end - start) / 1000)

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) return `${hours}h ${minutes}m`
    if (minutes > 0) return `${minutes}m ${secs}s`
    return `${secs}s`
  },

  // Get session summary
  getSummary(stats) {
    return {
      duration: this.formatDuration(stats.started_at, stats.stopped_at),
      records: stats.metrics.total_records,
      avgLatency: stats.metrics.avg_latency_ms?.toFixed(2),
      minLatency: stats.metrics.min_latency_ms?.toFixed(2),
      maxLatency: stats.metrics.max_latency_ms?.toFixed(2),
      avgPacketLoss: stats.metrics.avg_packet_loss?.toFixed(2),
    }
  },
}
