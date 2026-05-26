export default function HTTPCheckViewer({
  data,
  history,
  loading,
  onRun,
  useHttps,
  onHttpsChange,
  target,
}) {
  if (!target) {
    return (
      <div className="text-center text-slate-400 py-8">
        <p>Please select a target to run HTTP check</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Protocol Selection */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-2 text-slate-300">Protocol</label>
          <div className="flex gap-2">
            <button
              onClick={() => onHttpsChange(false)}
              className={`flex-1 py-2 px-3 rounded font-medium transition ${
                !useHttps
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              HTTP
            </button>
            <button
              onClick={() => onHttpsChange(true)}
              className={`flex-1 py-2 px-3 rounded font-medium transition ${
                useHttps
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              HTTPS
            </button>
          </div>
        </div>

        {/* Run Button */}
        <button
          onClick={onRun}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white font-medium py-2 px-6 rounded transition"
        >
          {loading ? 'Checking...' : '🌐 Check Status'}
        </button>
      </div>

      {/* Current Result */}
      {data && (
        <div className="space-y-4">
          <div className="bg-slate-800/50 border border-slate-700 rounded p-4">
            <h3 className="font-semibold mb-3">HTTP Check Result</h3>

            {/* Status Summary */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-slate-400 mb-1">URL</p>
                <p className="text-white font-mono text-sm break-all">{data.url}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Status</p>
                <p
                  className={`font-semibold text-lg ${
                    data.success ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {data.status_code ? (
                    <>
                      {data.status_code}
                      <span
                        className={`ml-2 text-sm ${
                          data.status_code >= 200 && data.status_code < 300
                            ? 'text-green-400'
                            : data.status_code >= 300 && data.status_code < 400
                              ? 'text-blue-400'
                              : 'text-red-400'
                        }`}
                      >
                        {data.status_code >= 200 && data.status_code < 300
                          ? '✓ OK'
                          : data.status_code >= 300 && data.status_code < 400
                            ? '→ Redirect'
                            : '✗ Error'}
                      </span>
                    </>
                  ) : (
                    '✗ Failed'
                  )}
                </p>
              </div>
            </div>

            {/* Response Time */}
            {data.response_time_ms !== null && (
              <div className="mb-4 p-3 bg-slate-700/30 rounded">
                <p className="text-sm text-slate-400 mb-1">Response Time</p>
                <p
                  className={`font-mono text-lg ${
                    data.response_time_ms > 5000
                      ? 'text-red-400'
                      : data.response_time_ms > 2000
                        ? 'text-yellow-400'
                        : 'text-green-400'
                  }`}
                >
                  {data.response_time_ms.toFixed(2)}ms
                </p>
              </div>
            )}

            {/* Error Message */}
            {data.error_message && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
                <p className="font-medium mb-1">Error</p>
                {data.error_message}
              </div>
            )}

            {/* SSL Information */}
            {useHttps && (
              <div className="bg-slate-700/20 border border-slate-600 rounded p-3 mb-4">
                <p className="text-sm font-semibold mb-2 text-slate-300">SSL Certificate</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-slate-400">Valid</p>
                    <p
                      className={`font-medium ${
                        data.ssl_valid === true
                          ? 'text-green-400'
                          : data.ssl_valid === false
                            ? 'text-red-400'
                            : 'text-slate-400'
                      }`}
                    >
                      {data.ssl_valid === true
                        ? '✓ Yes'
                        : data.ssl_valid === false
                          ? '✗ No'
                          : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-400">Expiry</p>
                    <p className="text-blue-300 font-mono text-xs">
                      {data.ssl_expiry_date || 'N/A'}
                    </p>
                  </div>
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
          <h3 className="font-semibold mb-3">Recent Checks</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {history.map((item, idx) => (
              <div key={idx} className="bg-slate-700/30 rounded p-2 text-sm">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-semibold ${
                          item.success
                            ? item.status_code >= 200 && item.status_code < 300
                              ? 'text-green-400'
                              : 'text-yellow-400'
                            : 'text-red-400'
                        }`}
                      >
                        {item.status_code || 'Failed'}
                      </span>
                      {item.response_time_ms && (
                        <span className="text-slate-400">
                          {item.response_time_ms}ms
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-slate-500 text-xs">
                    {new Date(item.checked_at).toLocaleTimeString()}
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
