"use client"

import { useState } from "react"
import SearchBar from "@/components/SearchBar"
import ResultsList from "@/components/ResultsList"
import IndexBuilder from "@/components/IndexBuilder"

export default function Home() {
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [responseTime, setResponseTime] = useState(undefined)
  const [hasSearched, setHasSearched] = useState(false)
  const [indexBuilt, setIndexBuilt] = useState(false)

    const handleSearch = async ({ q, k, file_name }) => {
        setIsLoading(true);
        setHasSearched(true);

        try {
            // Construir URL con query params
            const url = new URL("http://localhost:8000/search/");

            url.searchParams.append("q", q);
            url.searchParams.append("k", k);
            url.searchParams.append("file_name", file_name);

            console.log(url);

            const response = await fetch(url.toString(), {
                method: "GET", // tu backend usa POST, lo mantenemos
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                throw new Error("Search failed");
            }

            const data = await response.json();

            console.log(data);

            setResults(data.results || []);
            setResponseTime(data.execution_time || 0);

        } catch (error) {
            console.error("Error:", error);
            setResults([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleIndexBuilt = () => {
    setIndexBuilt(true)
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-gray-50">
      {/* Header Section */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Multimodal Information Retrieval System</h1>
          <p className="text-lg text-gray-600">Text Search</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sidebar with Search and Index Builder */}
          <div className="lg:col-span-1 space-y-6">
            {/* Search Card */}
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Search</h2>
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </div>

            {/* Index Builder Card */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <IndexBuilder onIndexBuilt={handleIndexBuilt} />
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6">
              {!hasSearched ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-base">Enter a query and click Search to get started</p>
                </div>
              ) : (
                <ResultsList results={results} isLoading={isLoading} responseTime={responseTime} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">Built with Next.js 14, React 18, and TailwindCSS 3</p>
        </div>
      </footer>
    </main>
  )
}
