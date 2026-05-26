export default function BandwidthTestViewer({
  data,
  history,
  loading,
  onRun,
  testSize,
  onTestSizeChange,
  target,
}) {
  if (!target) {
    return (
      <div className="text-center text-slate-400 py-8">
        <p>Please select a target to run bandwidth test</p>
      </div>
    )
  }

  const getSpeedColor = (mbps) => {
    if (!mbps) return 'text-slate-400'
    if (mbps > 100) return 'text-green-400'
    if (mbps > 50) return 'text-green-400'
    if (mbps > 20) return 'text-yellow-400'
    if (mbps > 5) return 'text-yellow-400'
    return 'text-red-400'
  }

  return (
    <div className="space-y-4">
      {/* Test Size Selection */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-2 text-slate-300">Test Size (MB)</label>
          <select
            value={testSize}
            onChange={(e) => onTestSizeChange(parseFloat(e.target.value))}
            disabled={loading}
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-slate-100 disabled:bg-slate-700"
          >
            <option value={5}>5 MB (Fast)</option>
            <option value={10}>10 MB (Standard)</option>
            <option value={25}>25 MB</option>
            <option value={50}>50 MB</option>
            <option value={100}>100 MB (Detailed)</option>
          </select>
        </div>

        {/* Run Button */}
        <button
          onClick={onRun}
          disabled={loading}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white font-medium py-2 px-6 rounded transition"
        >
          {loading ? `Testing... (est. ${testSize * 2}s)` : '⚡ Start Test'}
        </button>
      </div>

      {/* Current Result */}
      {data && (
        <div className="space-y-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold mb-3">Bandwidth Test Result</h3>

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

            {/* Error Message */}
            {data.error_message && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
                {data.error_message}
              </div>
            )}

            {/* Speed Display */}
            {data.download_speed_mbps !== null && (
              <div className="grid grid-cols-2 gap-4 mb-4">
                {/* Download Speed */}
                <div className="bg-slate-700/30 rounded p-4 text-center">
                  <p className="text-sm text-slate-400 mb-2">Download Speed</p>
                  <p className={`text-3xl font-bold ${getSpeedColor(data.download_speed_mbps)}`}>
                    {data.download_speed_mbps.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">Mbps</p>
                </div>

                {/* Test Duration */}
                <div className="bg-slate-700/30 rounded p-4 text-center">
                  <p className="text-sm text-slate-400 mb-2">Duration</p>
                  <p className="text-2xl font-bold text-slate-300">
                    {data.test_duration_seconds.toFixed(1)}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">seconds</p>
                </div>
              </div>
            )}

            {/* Data Transferred */}
            {data.bytes_transferred !== null && (
              <div className="bg-slate-700/20 border border-slate-600 rounded p-3 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400 mb-1">Bytes Transferred</p>
                    <p className="text-slate-300 font-mono">
                      {(data.bytes_transferred / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400 mb-1">Test Size</p>
                    <p className="text-slate-300 font-mono">{data.test_size_mb} MB</p>
                  </div>
                </div>
              </div>
            )}

            {/* Speed Gauge */}
            {data.download_speed_mbps !== null && (
              <div className="mb-4">
                <p className="text-xs text-slate-400 mb-2">Speed Gauge</p>
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      data.download_speed_mbps > 100
                        ? 'bg-green-500'
                        : data.download_speed_mbps > 50
                          ? 'bg-green-400'
                          : data.download_speed_mbps > 20
                            ? 'bg-yellow-400'
                            : data.download_speed_mbps > 5
                              ? 'bg-orange-400'
                              : 'bg-red-400'
                    }`}
                    style={{
                      width: `${Math.min((data.download_speed_mbps / 200) * 100, 100)}%`,
                    }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>0</span>
                  <span>100</span>
                  <span>200+ Mbps</span>
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
          <h3 className="font-semibold mb-3">Recent Tests</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {history.map((item, idx) => (
              <div key={idx} className="bg-slate-700/30 rounded p-3 text-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-slate-400">{item.test_size_mb} MB</span>
                  <span className="text-slate-500 text-xs">
                    {new Date(item.tested_at).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-slate-300">Download</span>
                      <span className={`font-semibold ${getSpeedColor(item.download_speed_mbps)}`}>
                        {item.download_speed_mbps
                          ? `${item.download_speed_mbps.toFixed(1)} Mbps`
                          : 'Failed'}
                      </span>
                    </div>
                    {item.download_speed_mbps && (
                      <div className="w-full bg-slate-600 rounded h-1.5">
                        <div
                          className={`h-full rounded ${getSpeedColor(item.download_speed_mbps).replace(
                            'text',
                            'bg',
                          )}`}
                          style={{
                            width: `${Math.min((item.download_speed_mbps / 200) * 100, 100)}%`,
                          }}
                        ></div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
