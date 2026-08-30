import { useState } from 'react'

export default function LearnMore({ children }) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--color-indigo)]
          hover:text-[var(--color-indigo-dark)] focus-visible:outline focus-visible:outline-2
          focus-visible:outline-offset-2 focus-visible:outline-[var(--color-indigo)] rounded transition-colors"
      >
        <span
          className="flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-indigo-soft)] border border-[var(--color-indigo)]/25 text-[10px] font-bold leading-none"
          aria-hidden="true"
        >
          i
        </span>
        {open ? 'Hide context' : 'Why this matters'}
      </button>
      {open && (
        <div className="mt-2.5 p-3 rounded-xl bg-[var(--color-line-soft)]/70 border border-[var(--color-line)] text-xs text-[var(--color-ink-soft)] leading-relaxed">
          {children}
        </div>
      )}
    </div>
  )
}
