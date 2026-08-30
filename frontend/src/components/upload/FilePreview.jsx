import Card from '../common/Card'
import Button from '../common/Button'

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function FilePreview({ file, onRemove, onContinue }) {
  return (
    <Card className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div className="flex items-center gap-3.5 min-w-0">
        <div className="shrink-0 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-signal-red-soft)] text-[var(--color-signal-red)] font-mono text-xs font-bold border border-[var(--color-signal-red)]/20 shadow-xs">
          PDF
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-[var(--color-ink)] truncate">{file.name}</p>
          <p className="text-xs text-[var(--color-ink-faint)] font-mono mt-0.5">{formatSize(file.size)}</p>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0 w-full sm:w-auto justify-end">
        <button
          type="button"
          onClick={onRemove}
          className="text-xs font-medium text-[var(--color-ink-faint)] hover:text-[var(--color-signal-red)] px-3 py-1.5 transition-colors"
        >
          Remove
        </button>
        <Button onClick={onContinue}>
          Start Analysis →
        </Button>
      </div>
    </Card>
  )
}
