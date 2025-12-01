"use client"

export default function ResultCard({ result, index }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-6">
      {/* Result Index and Score */}
      <div className="flex items-start justify-between mb-4">
        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
          Result #{index}
        </span>
        <div className="text-right">
          <span className="text-xs text-gray-500 block mb-1">Relevance Score</span>
          <span className="text-lg font-bold text-green-600">
            {result.score ? (result.score * 100).toFixed(1) : "N/A"}%
          </span>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">{result.title || "Untitled"}</h3>

      {/* Artist */}
      {result.artist && (
        <p className="text-sm text-gray-600 mb-3">
          <span className="font-semibold">Artist:</span> {result.artist}
        </p>
      )}

      {/* Snippet */}
      {result.snippet && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-1">Snippet</p>
          <p className="text-sm text-gray-700 line-clamp-3 bg-gray-50 p-3 rounded border border-gray-100">
            {result.snippet}
          </p>
        </div>
      )}

      {/* Response Time */}
      {result.responseTime !== undefined && (
        <div className="pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-500">
            Response Time: <span className="font-semibold">{result.responseTime}ms</span>
          </span>
        </div>
      )}
    </div>
  )
}
