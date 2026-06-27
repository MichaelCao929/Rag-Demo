import { FileText } from 'lucide-react'
import type { Message } from '../App'

type Props = { message: Message }

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-navy text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        {/* Answer text */}
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-sm">
          {message.content || (message.streaming && (
            <span className="inline-flex gap-1 items-center text-slate-400">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </span>
          ))}
          {message.streaming && message.content && (
            <span className="inline-block w-0.5 h-4 bg-navy ml-0.5 animate-pulse align-middle" />
          )}
        </div>

        {/* Source citations */}
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {message.sources.map((s, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-full"
              >
                <FileText size={11} className="text-navy" />
                [{i + 1}] {s.file}
                {s.page !== '?' && <span className="text-slate-400">p.{s.page}</span>}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
