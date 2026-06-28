import { useState } from 'react'
import { FileText, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import type { Message, Source } from '../App'

function SourceBadge({ source, index }: { source: Source; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const hasText = Boolean(source.text)

  return (
    <div>
      <button
        onClick={() => hasText && setExpanded(v => !v)}
        className={`
          inline-flex items-center gap-1.5 bg-slate-100 text-slate-600 text-xs px-2.5 py-1 rounded-full
          transition-colors
          ${hasText ? 'hover:bg-slate-200 cursor-pointer' : 'cursor-default'}
        `}
      >
        <FileText size={11} className="text-navy flex-shrink-0" />
        <span className="font-medium">[{index + 1}]</span>
        <span className="truncate max-w-[140px]">{source.file}</span>
        {source.page !== '?' && (
          <span className="text-slate-400 flex-shrink-0">p.{source.page}</span>
        )}
        {hasText && (
          expanded
            ? <ChevronUp size={11} className="flex-shrink-0 text-slate-400" />
            : <ChevronDown size={11} className="flex-shrink-0 text-slate-400" />
        )}
      </button>

      {expanded && source.text && (
        <div className="mt-1.5 text-xs text-slate-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5 leading-relaxed">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-amber-500 mb-1.5">
            Retrieved chunk
          </p>
          <p className="whitespace-pre-wrap">{source.text}</p>
        </div>
      )}
    </div>
  )
}

export default function MessageBubble({ message }: { message: Message }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const copy = async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

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
        {/* Answer bubble */}
        <div className="relative group bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <p className="text-sm leading-relaxed text-slate-800 pr-6">
            {message.content || (message.streaming && (
              <span className="inline-flex gap-1 items-center text-slate-400">
                <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:300ms]" />
              </span>
            ))}
            {message.streaming && message.content && (
              <span className="inline-block w-0.5 h-4 bg-navy ml-0.5 animate-pulse align-middle" />
            )}
          </p>

          {/* Copy button — fades in on hover, only after streaming is done */}
          {!message.streaming && message.content && (
            <button
              onClick={copy}
              title="Copy answer"
              className="absolute top-2.5 right-2.5 p-1.5 rounded-md text-slate-400 opacity-0 group-hover:opacity-100 hover:bg-slate-100 hover:text-slate-600 transition-all"
            >
              {copied
                ? <Check size={13} className="text-green-500" />
                : <Copy size={13} />
              }
            </button>
          )}
        </div>

        {/* Source citations — each expandable */}
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-col gap-1.5 px-1">
            {message.sources.map((s, i) => (
              <SourceBadge key={i} source={s} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
