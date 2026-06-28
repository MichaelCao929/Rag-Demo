import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, BookOpen, Trash2 } from 'lucide-react'
import MessageBubble from './MessageBubble'
import type { Message } from '../App'

type Props = {
  messages: Message[]
  onSend: (question: string) => void
  onClear: () => void
  loading: boolean
  hasDocuments: boolean
}

const SUGGESTIONS = [
  'What documents are in the knowledge base?',
  'Summarise the key findings.',
  'What are the eligibility criteria?',
]

export default function ChatWindow({ messages, onSend, onClear, loading, hasDocuments }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    onSend(q)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const onInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`
  }

  return (
    <main className="flex-1 flex flex-col overflow-hidden">
      {/* Top bar */}
      <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center gap-2 shadow-sm">
        <BookOpen size={16} className="text-navy" />
        <h1 className="text-sm font-semibold text-slate-800">Document Q&amp;A</h1>
        <span className="ml-auto flex items-center gap-3">
          <span className="text-xs text-slate-400">
            {hasDocuments ? 'Ready' : 'Upload a PDF to begin'}
          </span>
          {messages.length > 0 && (
            <button
              onClick={onClear}
              title="Clear conversation"
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-red-500 transition-colors px-2 py-1 rounded-md hover:bg-red-50"
            >
              <Trash2 size={13} />
              Clear
            </button>
          )}
        </span>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-6 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 select-none">
            <div className="w-14 h-14 rounded-full bg-slate-100 flex items-center justify-center mb-4">
              <BookOpen size={24} className="text-navy opacity-60" />
            </div>
            <p className="text-sm font-medium text-slate-600 mb-1">Ask anything about your documents</p>
            <p className="text-xs text-slate-400 mb-6">
              {hasDocuments
                ? 'Type a question below or try a suggestion.'
                : 'Upload a PDF from the sidebar first.'}
            </p>
            {hasDocuments && (
              <div className="flex flex-col gap-2 w-full max-w-sm">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => onSend(s)}
                    className="text-left text-xs bg-white border border-slate-200 hover:border-navy hover:text-navy rounded-lg px-4 py-2.5 transition-colors text-slate-600"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map(m => <MessageBubble key={m.id} message={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-200 px-4 py-3">
        <div className="flex items-end gap-2 max-w-3xl mx-auto bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 focus-within:border-navy focus-within:ring-1 focus-within:ring-navy transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={onInput}
            onKeyDown={onKeyDown}
            placeholder={hasDocuments ? 'Ask a question… (Enter to send)' : 'Upload a PDF first'}
            disabled={loading || !hasDocuments}
            className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 resize-none outline-none py-1 max-h-28 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading || !hasDocuments}
            className="flex-shrink-0 w-8 h-8 rounded-lg bg-navy text-white flex items-center justify-center hover:bg-navy-light disabled:opacity-40 disabled:cursor-not-allowed transition-colors mb-0.5"
          >
            <Send size={14} />
          </button>
        </div>
        <p className="text-center text-xs text-slate-300 mt-2">
          Answers are grounded in your documents — always verify important information.
        </p>
      </div>
    </main>
  )
}
