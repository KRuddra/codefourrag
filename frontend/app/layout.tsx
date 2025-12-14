import './globals.css'

export const metadata = {
  title: 'Wisconsin Law Enforcement Legal Chat',
  description: 'RAG system for querying legal documents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-bgPrimary text-dark-textPrimary">
        {children}
      </body>
    </html>
  )
}

