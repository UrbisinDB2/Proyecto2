"use client"

import { useState } from "react"

export default function IndexBuilder({ onIndexBuilt }) {
  const [file, setFile] = useState("")
  const [docIdIdx, setDocIdIdx] = useState(0)
  const [textColumnIdx, setTextColumnIdx] = useState(3)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState("")
  const [messageType, setMessageType] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setMessage("")

    try {
      const response = await fetch("https://localhost:8000/search/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          file: file.trim(),
          docIdIdx: Number.parseInt(docIdIdx),
          textColumnIdx: Number.parseInt(textColumnIdx),
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Index building failed")
      }

      setMessageType("success")
      setMessage(data.message || "Index built successfully!")
      setFile("")
      setDocIdIdx(0)
      setTextColumnIdx(3)
      onIndexBuilt && onIndexBuilt()
    } catch (error) {
      setMessageType("error")
      setMessage(error.message || "An error occurred")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-gray-900">Build Index</h3>

        {/* File Input */}
        <div>
          <label htmlFor="file" className="block text-sm font-semibold text-gray-700 mb-2">
            File Name
          </label>
          <input
            id="file"
            type="text"
            value={file}
            onChange={(e) => setFile(e.target.value)}
            placeholder="e.g., spotify_songs"
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
            disabled={isLoading}
            required
          />
        </div>

        {/* Doc ID Index */}
        <div>
          <label htmlFor="docIdIdx" className="block text-sm font-semibold text-gray-700 mb-2">
            Doc ID Column Index
          </label>
          <input
            id="docIdIdx"
            type="number"
            min="0"
            value={docIdIdx}
            onChange={(e) => setDocIdIdx(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        {/* Text Column Index */}
        <div>
          <label htmlFor="textColumnIdx" className="block text-sm font-semibold text-gray-700 mb-2">
            Text Column Index
          </label>
          <input
            id="textColumnIdx"
            type="number"
            min="0"
            value={textColumnIdx}
            onChange={(e) => setTextColumnIdx(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        {/* Status Message */}
        {message && (
          <div
            className={`p-3 rounded-lg text-sm font-medium ${
              messageType === "success"
                ? "bg-green-50 text-green-800 border border-green-200"
                : "bg-red-50 text-red-800 border border-red-200"
            }`}
          >
            {message}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !file.trim()}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 ease-in-out"
        >
          {isLoading ? "Building Index..." : "Build Index"}
        </button>
      </div>
    </form>
  )
}
