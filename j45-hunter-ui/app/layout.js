export const metadata = {
  title: 'J45 Hunter',
  description: 'Vintage Gibson J-45 listing monitor',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0 }}>
        {children}
      </body>
    </html>
  )
}
