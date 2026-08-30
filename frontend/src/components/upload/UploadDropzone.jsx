import { useRef, useState } from 'react'

export default function UploadDropzone({ onFileSelected }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (files) => {
    if (files && files[0]) onFileSelected(files[0])
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      className={`rounded-2xl border-2 border-dashed p-10 sm:p-14 text-center transition-all duration-200 cursor-pointer
        ${
          isDragging
            ? 'border-[var(--color-indigo)] bg-[var(--color-indigo-soft)] scale-[1.01]'
            : 'border-[var(--color-line)] bg-[var(--color-paper-raised)] hover:border-[var(--color-indigo)]/50'
        }`}
      onClick={() => inputRef.current?.click()}
    >
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] mb-4 border border-[var(--color-indigo)]/20 shadow-xs">
        <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 16V4m0 0L7 9m5-5l5 5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      <p className="font-display text-lg font-semibold text-[var(--color-ink)]">
        Upload Official DRHP PDF
      </p>

      <p className="mt-1.5 text-sm text-[var(--color-ink-soft)]">
        Drag & drop your prospectus here, or{' '}
        <span className="text-[var(--color-indigo)] font-semibold underline underline-offset-2">
          browse files
        </span>
      </p>

      <div className="mt-4 flex items-center justify-center gap-2">
        <span className="text-[11px] font-mono text-[var(--color-ink-faint)] bg-[var(--color-line-soft)] px-2.5 py-1 rounded-md border border-[var(--color-line)]">
          PDF format
        </span>
        <span className="text-[11px] font-mono text-[var(--color-ink-faint)] bg-[var(--color-line-soft)] px-2.5 py-1 rounded-md border border-[var(--color-line)]">
          Up to 50 MB
        </span>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  )
}
