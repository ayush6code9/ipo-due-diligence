import Card from '../common/Card'

export default function UploadProgress({ fileName, progress }) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-semibold text-[var(--color-ink)] truncate">{fileName}</p>
        <p className="text-xs font-mono font-semibold text-[var(--color-indigo)] shrink-0">{progress}%</p>
      </div>
      <div className="mt-3 h-2 rounded-full bg-[var(--color-line-soft)] overflow-hidden">
        <div
          className="h-full rounded-full bg-[var(--color-indigo)] transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-3 text-xs text-[var(--color-ink-soft)] flex items-center gap-2">
        <span className="h-2 w-2 rounded-full bg-[var(--color-indigo)] animate-pulse" />
        {progress < 100 ? 'Uploading DRHP prospectus…' : 'Extracting text and verifying structure…'}
      </p>
    </Card>
  )
}
