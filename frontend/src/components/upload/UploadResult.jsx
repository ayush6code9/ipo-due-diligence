import Card from '../common/Card'
import Button from '../common/Button'
import StatusBadge from '../common/StatusBadge'

const STATUS_COPY = {
  success: { label: 'Fully Readable', level: 'strong' },
  partial: { label: 'Mostly readable', level: 'moderate' },
  no_extractable_text: { label: 'Scanned / Low text', level: 'high-risk' },
}

export default function UploadResult({ result, onContinue }) {
  const { original_filename, page_count, extracted_pages, pages_with_little_text, status } = result
  const badge = STATUS_COPY[status] || STATUS_COPY.partial

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[var(--color-ink)]">DRHP Uploaded Successfully</p>
          <p className="text-xs text-[var(--color-ink-faint)] font-mono mt-0.5 truncate">{original_filename}</p>
        </div>
        <StatusBadge label={badge.label} level={badge.level} size="sm" />
      </div>

      <div className="mt-4 pt-4 border-t border-[var(--color-line-soft)] space-y-2 text-sm text-[var(--color-ink-soft)]">
        <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-[var(--color-line-soft)]/50 border border-[var(--color-line)]">
          <div>
            <p className="text-[10px] font-mono uppercase text-[var(--color-ink-faint)]">Total Pages</p>
            <p className="font-display text-lg font-bold text-[var(--color-ink)] mt-0.5">{page_count}</p>
          </div>
          <div>
            <p className="text-[10px] font-mono uppercase text-[var(--color-ink-faint)]">Readable Pages</p>
            <p className="font-display text-lg font-bold text-[var(--color-signal-green)] mt-0.5">{extracted_pages}</p>
          </div>
        </div>

        {pages_with_little_text.length > 0 && (
          <p className="text-xs text-[var(--color-ink-faint)] mt-2">
            Little or no text on page{pages_with_little_text.length > 1 ? 's' : ''}{' '}
            {pages_with_little_text.join(', ')} — likely scanned tables or signatures.
          </p>
        )}
      </div>

      <div className="mt-5 pt-3 border-t border-[var(--color-line-soft)]">
        <Button onClick={onContinue} className="w-full sm:w-auto">
          Proceed to Analysis Dashboard →
        </Button>
      </div>
    </Card>
  )
}
