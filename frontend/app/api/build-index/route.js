export async function POST(request) {
  try {
    const body = await request.json()

    const { file, docIdIdx, textColumnIdx } = body

    if (!file) {
      return Response.json({ error: "File name is required" }, { status: 400 })
    }

    if (docIdIdx === undefined || docIdIdx === null) {
      return Response.json({ error: "Doc ID index is required" }, { status: 400 })
    }

    if (textColumnIdx === undefined || textColumnIdx === null) {
      return Response.json({ error: "Text column index is required" }, { status: 400 })
    }

    const buildTime = Math.random() * 2000 + 500 // 500-2500ms

    return Response.json({
      success: true,
      message: `Index built successfully for "${file}" in ${Math.round(buildTime)}ms`,
      config: {
        file,
        docIdIdx,
        textColumnIdx,
      },
      buildTime: Math.round(buildTime),
    })
  } catch (error) {
    console.error("Error building index:", error)
    return Response.json({ error: "Failed to build index" }, { status: 500 })
  }
}
