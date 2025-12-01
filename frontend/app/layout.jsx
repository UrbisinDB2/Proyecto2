import "./globals.css"

export const metadata = {
  title: "Multimodal Information Retrieval System",
  description: "Text Search Interface",
    generator: 'v0.app'
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
