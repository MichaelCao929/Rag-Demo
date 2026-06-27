import { useRef, useState, DragEvent } from 'react'
import { FileText, Upload, Loader2, BookOpen } from 'lucide-react'

type Props = {
  documents: string[]
  onUploadComplete: () => void
}

export default function Sidebar({ documents, onUploadComplete }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [toast, setToast] = useState<{ text: string; ok: boolean } | null>(null)

  const showToast = (text: string, ok: boolean) => {
    setToast({ text, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const uploadFile = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      showToast('Only PDF files are supported.', false)
      return
    }
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Upload failed')
      showToast(`${data.filename} — ${data.chunks} chunks indexed`, true)
      onUploadComplete()
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Upload failed', false)
    } finally {
      setUploading(false)
    }
  }

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
    e.target.value = ''
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) uploadFile(file)
  }

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col bg-white border-r border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-navy px-4 py-5">
        <div className="flex items-center gap-2 text-white">
          <BookOpen size={18} />
          <span className="font-semibold text-sm tracking-wide">RAG Knowledge Base</span>
        </div>
        <p className="text-navy-light text-xs mt-1 text-blue-200">
          {documents.length} document{documents.length !== 1 ? 's' : ''} indexed
        </p>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-3 py-3">
        {documents.length === 0 ? (
          <p className="text-xs text-slate-400 text-center mt-6 px-2 leading-relaxed">
            No documents yet.<br />Upload a PDF to get started.
          </p>
        ) : (
          <ul className="space-y-1">
            {documents.map(doc => (
              <li
                key={doc}
                className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-slate-50 group"
              >
                <FileText size={14} className="text-navy flex-shrink-0" />
                <span className="text-xs text-slate-600 truncate" title={doc}>{doc}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Upload area */}
      <div className="p-3 border-t border-slate-200">
        <div
          className={`
            border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
            ${dragOver
              ? 'border-navy bg-blue-50'
              : 'border-slate-200 hover:border-navy hover:bg-slate-50'
            }
            ${uploading ? 'pointer-events-none opacity-60' : ''}
          `}
          onClick={() => inputRef.current?.click()}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          {uploading ? (
            <Loader2 size={18} className="animate-spin mx-auto text-navy mb-1" />
          ) : (
            <Upload size={18} className="mx-auto text-slate-400 mb-1" />
          )}
          <p className="text-xs text-slate-500">
            {uploading ? 'Indexing...' : 'Drop PDF or click to upload'}
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={onInputChange}
        />

        {/* Toast */}
        {toast && (
          <div className={`
            mt-2 px-3 py-2 rounded-md text-xs
            ${toast.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}
          `}>
            {toast.text}
          </div>
        )}
      </div>
    </aside>
  )
}
