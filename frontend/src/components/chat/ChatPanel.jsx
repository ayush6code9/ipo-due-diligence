import { useState } from 'react'
import Card from '../common/Card'
import SuggestedQuestions from './SuggestedQuestions'
import { chatWithDocument } from '../../services/api'

const PLACEHOLDER_REPLY =
  "Chat with your DRHP is available when analyzing an ingested prospectus. In full analysis mode, responses cite exact document page references."

export default function ChatPanel({ suggestions, documentId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const ask = async (question) => {
    const q = question.trim()
    if (!q || loading) return

    setMessages((prev) => [...prev, { role: 'user', text: q }])
    setInput('')

    if (!documentId) {
      setMessages((prev) => [...prev, { role: 'assistant', text: PLACEHOLDER_REPLY }])
      return
    }

    setLoading(true)
    try {
      const result = await chatWithDocument(documentId, q)
      const sourceRefs = (result.sources || [])
        .filter((s) => s.page_start)
        .map((s) => {
          let ref = `Pages ${s.page_start}–${s.page_end}`
          if (s.section) ref += ` (${s.section})`
          return ref
        })

      let answerText = result.answer || 'No answer was generated.'
      if (sourceRefs.length > 0) {
        answerText += `\n\n📄 Sources: ${sourceRefs.join(', ')}`
      }

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: answerText, llmUsed: result.llm_used },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `Sorry, something went wrong: ${err.message || 'Unknown error'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <div className="flex items-center justify-between pb-3 border-b border-[var(--color-line-soft)]">
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">RAG Document Assistant</p>
          <p className="text-sm font-semibold text-[var(--color-ink)] mt-0.5">Query the DRHP Prospectus</p>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] border border-[var(--color-indigo)]/15">
          Semantic Search
        </span>
      </div>

      <div className="mt-4 space-y-3 max-h-80 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="text-center py-6 px-4 rounded-xl bg-[var(--color-line-soft)]/40 border border-[var(--color-line)]">
            <p className="text-xs sm:text-sm text-[var(--color-ink-soft)]">
              Ask specific questions about promoter background, revenue streams, litigations, or debt terms.
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-xs sm:text-sm rounded-2xl px-4 py-3 max-w-[85%] leading-relaxed whitespace-pre-line shadow-xs ${
              m.role === 'user'
                ? 'bg-[var(--color-indigo)] text-white ml-auto rounded-tr-xs'
                : 'bg-[var(--color-line-soft)] text-[var(--color-ink)] border border-[var(--color-line)] rounded-tl-xs'
            }`}
          >
            {m.text}
          </div>
        ))}
        {loading && (
          <div className="inline-flex items-center gap-2 text-xs font-medium text-[var(--color-indigo)] bg-[var(--color-indigo-soft)] px-3 py-1.5 rounded-full border border-[var(--color-indigo)]/20">
            <span className="h-2 w-2 rounded-full bg-[var(--color-indigo)] animate-pulse" />
            Searching vector index and extracting citations…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          ask(input)
        }}
        className="mt-4 flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this prospectus…"
          disabled={loading}
          className="flex-1 rounded-full border border-[var(--color-line)] bg-[var(--color-paper-raised)]
            px-4 py-2.5 text-xs sm:text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)]
            focus:outline-none focus:ring-2 focus:ring-[var(--color-indigo)]/40 focus:border-[var(--color-indigo)]
            shadow-xs disabled:opacity-50 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-full bg-[var(--color-indigo)] text-white px-5 py-2.5 text-xs sm:text-sm font-semibold
            hover:bg-[var(--color-indigo-dark)] transition-colors disabled:opacity-40 active:scale-[0.98]"
        >
          Ask
        </button>
      </form>

      {suggestions && suggestions.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[var(--color-line-soft)]">
          <p className="text-[11px] font-mono text-[var(--color-ink-faint)] uppercase mb-2">Suggested Inquiries</p>
          <SuggestedQuestions questions={suggestions} onPick={ask} />
        </div>
      )}
    </Card>
  )
}
