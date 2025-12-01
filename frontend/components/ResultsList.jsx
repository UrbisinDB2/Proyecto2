"use client"

import ResultCard from "./ResultCard"

export default function ResultsList({ results, isLoading, responseTime }) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-200 border-t-blue-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Searching...</p>
        </div>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No results yet. Try searching to get started!</p>
      </div>
    )
  }

  console.log(results);

  return (
    <div className="space-y-6">
      {/* Results Header */}
      <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div>
          <p className="text-sm text-gray-600">
            Found <span className="font-bold text-blue-600">{results.length}</span> results
          </p>
        </div>
        {responseTime !== undefined && (
          <div className="text-right">
            <p className="text-sm text-gray-600">
              Response time: <span className="font-bold text-blue-600">{responseTime}ms</span>
            </p>
          </div>
        )}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map((result, index) => (
          <ResultCard key={index} result={result} index={index + 1} />
        ))}
      </div>
    </div>
  )
}
