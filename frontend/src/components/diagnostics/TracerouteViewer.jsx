export default function TracerouteViewer({ data, history, loading, onRun, target }) {
  if (!target) {
    return (
      <div className="text-center text-slate-400 py-8">
        <p>Please select a target to run traceroute</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Run Button */}
      <button
        onClick={onRun}
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium py-2 px-4 rounded transition"
      >
        {loading ? 'Running Traceroute...' : '🗺️ Start Traceroute'}
      </button>

      {/* Current Result */}
      {data && (
        <div className="space-y-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold mb-3">Traceroute Result</h3>

            {/* Status */}
            <div className="mb-4 flex justify-between items-start">
              <div>
                <p className="text-sm text-slate-400">Target</p>
                <p className="text-white font-mono">{data.target}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400">Status</p>
                <p
                  className={`font-semibold ${
                    data.success ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {data.success ? '✓ Success' : '✗ Failed'}
                </p>
              </div>
            </div>

            {data.error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
                {data.error}
              </div>
            )}

            {data.target_ip && (
              <div className="mb-4 text-sm">
                <p className="text-slate-400">Resolved IP</p>
                <p className="text-blue-300 font-mono">{data.target_ip}</p>
              </div>
            )}

            {/* Hops Table */}
            {data.hops && data.hops.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-semibold mb-3 text-slate-300">
                  Hops ({data.total_hops})
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left py-2 px-2 text-slate-400">Hop</th>
                        <th className="text-left py-2 px-2 text-slate-400">IP</th>
                        <th className="text-left py-2 px-2 text-slate-400">Hostname</th>
                        <th className="text-right py-2 px-2 text-slate-400">Latency</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.hops.map((hop, idx) => (
                        <tr key={idx} className="border-b border-slate-800 hover:bg-slate-700/30">
                          <td className="py-2 px-2 text-slate-300">{hop.hop || idx + 1}</td>
                          <td className="py-2 px-2 text-blue-300 font-mono text-xs">
                            {hop.ip}
                          </td>
                          <td className="py-2 px-2 text-slate-400 text-xs truncate">
                            {hop.hostname || '-'}
                          </td>
                          <td className="py-2 px-2 text-right">
                            {hop.latency_ms !== null ? (
                              <span
                                className={`font-mono ${
                                  hop.latency_ms > 50
                                    ? 'text-red-400'
                                    : hop.latency_ms > 20
                                      ? 'text-yellow-400'
                                      : 'text-green-400'
                                }`}
                              >
                                {hop.latency_ms}ms
                              </span>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {data.timestamp && (
              <p className="text-xs text-slate-500 mt-4">
                {new Date(data.timestamp).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
          <h3 className="font-semibold mb-3">Recent Traceroutes</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {history.map((item, idx) => (
              <div key={idx} className="bg-slate-700/30 rounded p-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">
                    {item.total_hops} hops
                    <span
                      className={`ml-2 ${item.success ? 'text-green-400' : 'text-red-400'}`}
                    >
                      {item.success ? '✓' : '✗'}
                    </span>
                  </span>
                  <span className="text-slate-500 text-xs">
                    {new Date(item.completed_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
