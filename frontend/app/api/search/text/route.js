export async function POST(request) {
  try {
    const body = await request.json()
    const { q, k, file_name } = body

    if (!q || k === undefined || !file_name) {
      return Response.json({ error: "Missing q, k, or file_name parameter" }, { status: 400 })
    }

    // Simulate API processing time
    const startTime = Date.now()
    await new Promise((resolve) => setTimeout(resolve, Math.random() * 1000 + 500))
    const responseTime = Date.now() - startTime

    // Mock results data
    const mockResults = [
      {
        title: "Understanding Information Retrieval Systems",
        artist: "Dr. Jane Smith",
        snippet:
          "Information retrieval is the process of finding relevant documents or information from large collections. Modern systems use advanced algorithms to rank and return the most relevant results.",
        score: 0.95,
      },
      {
        title: "Machine Learning for Search",
        artist: "Prof. John Davis",
        snippet:
          "Machine learning techniques have revolutionized search systems by enabling better ranking and personalization. Neural networks can now understand semantic meaning beyond keyword matching.",
        score: 0.88,
      },
      {
        title: "Multimodal Search Technologies",
        artist: "Dr. Sarah Johnson",
        snippet:
          "Multimodal search combines text, images, and audio data to provide comprehensive retrieval results. This approach helps users find information across different data types simultaneously.",
        score: 0.82,
      },
      {
        title: "Optimizing Search Performance",
        artist: "Tech Research Team",
        snippet:
          "Search performance optimization involves indexing strategies, caching mechanisms, and distributed computing. Achieving sub-second response times requires careful architectural planning.",
        score: 0.78,
      },
      {
        title: "Natural Language Processing in Search",
        artist: "Dr. Mike Chen",
        snippet:
          "NLP techniques enable search systems to understand user intent and context. Query understanding is crucial for delivering relevant results in modern search engines.",
        score: 0.75,
      },
      {
        title: "Query Expansion Techniques",
        artist: "Research Lab",
        snippet:
          "Query expansion improves recall by adding related terms to the original search query. This technique helps users find relevant content they might not have thought to search for.",
        score: 0.72,
      },
    ]

    // Return top k results
    const results = mockResults.slice(0, Math.min(k, mockResults.length)).map((result) => ({
      ...result,
      responseTime,
    }))

    return Response.json({
      results,
      responseTime,
      q,
      k,
      file_name,
      total: results.length,
    })
  } catch (error) {
    console.error("Search error:", error)
    return Response.json({ error: "Internal server error" }, { status: 500 })
  }
}
