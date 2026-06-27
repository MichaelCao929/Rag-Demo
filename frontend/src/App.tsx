import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'

export type Source = { file: string; page: number | string }

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  streaming?: boolean
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [documents, setDocuments] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch('/api/sources')
      const data = await res.json()
      setDocuments(data.documents ?? [])
    } catch {
      /* backend not ready yet */
    }
  }, [])

  useEffect(() => { fetchDocuments() }, [fetchDocuments])

  const sendMessage = async (question: string) => {
    const userId = crypto.randomUUID()
    const assistantId = crypto.randomUUID()

    setMessages(prev => [
      ...prev,
      { id: userId, role: 'user', content: question },
      { id: assistantId, role: 'assistant', content: '', streaming: true },
    ])
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          const payload = JSON.parse(raw)

          if (payload.type === 'sources') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId ? { ...m, sources: payload.sources } : m
            ))
          } else if (payload.type === 'text') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId
                ? { ...m, content: m.content + payload.text }
                : m
            ))
          } else if (payload.type === 'done') {
            setMessages(prev => prev.map(m =>
              m.id === assistantId ? { ...m, streaming: false } : m
            ))
          }
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === assistantId
          ? { ...m, content: 'Something went wrong. Make sure the backend is running.', streaming: false }
          : m
      ))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-slate-50 font-sans overflow-hidden">
      <Sidebar documents={documents} onUploadComplete={fetchDocuments} />
      <ChatWindow
        messages={messages}
        onSend={sendMessage}
        loading={loading}
        hasDocuments={documents.length > 0}
      />
    </div>
  )
}
