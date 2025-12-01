"use client"

import { useState } from "react"

export default function SearchBar({ onSearch, isLoading }) {
  const [query, setQuery] = useState("")
  const [topK, setTopK] = useState(10)
  const [fileName, setFileName] = useState("spotify_songs")

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch({
        q: query.trim(),
        k: Number.parseInt(topK),
        file_name: fileName.trim(),
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="space-y-4">
        {/* Query Input */}
        <div>
          <label htmlFor="query" className="block text-sm font-semibold text-gray-700 mb-2">
            Search Query
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your text search..."
            className="w-full p-4 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows="6"
            disabled={isLoading}
          />
        </div>

        {/* File Name Input */}
        <div>
          <label htmlFor="fileName" className="block text-sm font-semibold text-gray-700 mb-2">
            File Name
          </label>
          <input
            id="fileName"
            type="text"
            value={fileName}
            onChange={(e) => setFileName(e.target.value)}
            placeholder="e.g., spotify_songs"
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        {/* Top-K Input */}
        <div>
          <label htmlFor="topK" className="block text-sm font-semibold text-gray-700 mb-2">
            Top K Results
          </label>
          <input
            id="topK"
            type="number"
            min="1"
            max="100"
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        {/* Search Button */}
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 ease-in-out"
        >
          {isLoading ? "Searching..." : "Search"}
        </button>
      </div>
    </form>
  )
}
