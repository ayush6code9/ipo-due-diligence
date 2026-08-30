import Card from '../common/Card'
import Button from '../common/Button'

export default function UploadError({ message, onRetry }) {
  return (
    <Card className="border-[var(--color-signal-red)]/30 bg-[var(--color-signal-red-soft)]">
      <div className="flex items-start gap-3">
        <div className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-signal-red)]/20 text-[var(--color-signal-red)] font-bold text-sm">
          !
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-[var(--color-signal-red)]">Upload failed</p>
          <p className="text-xs text-[var(--color-ink-soft)] mt-1 leading-relaxed">
            {message || 'The DRHP document could not be processed. Please verify the file is a valid PDF under 50 MB.'}
          </p>
          <div className="mt-4">
            <Button variant="secondary" onClick={onRetry} className="text-xs py-2 px-4">
              Try again
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
