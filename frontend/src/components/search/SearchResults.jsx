import Card from '../common/Card'

const STATUS_STYLE = {
  Open: 'text-[var(--color-signal-green)] bg-[var(--color-signal-green-soft)] border-[var(--color-signal-green)]/25',
  Upcoming: 'text-[var(--color-indigo)] bg-[var(--color-indigo-soft)] border-[var(--color-indigo)]/25',
  Closed: 'text-[var(--color-ink-faint)] bg-[var(--color-line-soft)] border-[var(--color-line)]',
  Listed: 'text-[var(--color-ink-faint)] bg-[var(--color-line-soft)] border-[var(--color-line)]',
}

export default function SearchResults({
  results = [],
  loading = false,
  error = null,
  query = '',
  onSelect,
  onUploadFallback,
  onRetry,
}) {
  if (loading) {
    return (
      <div className="mt-8 text-center py-8">
        <div className="inline-flex items-center gap-2.5 text-sm text-[var(--color-ink-soft)] font-medium">
          <span className="h-4 w-4 rounded-full border-2 border-[var(--color-indigo)] border-t-transparent animate-spin" />
          Searching IPO records&hellip;
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-6 p-5 rounded-2xl bg-[var(--color-signal-red-soft)] border border-[var(--color-signal-red)]/20">
        <div className="flex items-start gap-3">
          <span className="text-[var(--color-signal-red)] font-bold">⚠</span>
          <div className="flex-1">
            <p className="text-sm text-[var(--color-signal-red)] font-semibold">Search unavailable</p>
            <p className="text-xs text-[var(--color-ink-soft)] mt-1">{error}</p>
            <div className="mt-3 flex items-center gap-4">
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="text-xs text-[var(--color-ink)] hover:text-[var(--color-indigo)] font-semibold underline underline-offset-2"
                >
                  Retry search
                </button>
              )}
              <button
                type="button"
                onClick={onUploadFallback}
                className="text-xs text-[var(--color-indigo)] hover:underline font-semibold"
              >
                Upload DRHP manually instead →
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="mt-8 text-center py-8 px-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-paper-raised)]">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-[var(--color-line-soft)] text-[var(--color-ink-faint)] mb-3">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <p className="text-sm text-[var(--color-ink)] font-semibold">
          No matching IPOs found{query ? ` for “${query}”` : ''}.
        </p>
        <p className="text-xs text-[var(--color-ink-soft)] mt-1.5 max-w-sm mx-auto">
          Try searching with another company name, or{' '}
          <button
            type="button"
            onClick={onUploadFallback}
            className="text-[var(--color-indigo)] hover:underline font-semibold"
          >
            upload the DRHP PDF directly
          </button>
          .
        </p>
      </div>
    )
  }

  return (
    <div className="mt-6 space-y-3.5">
      {results.map((ipo, idx) => (
        <Card
          key={`${ipo.company_name}-${idx}`}
          padded={false}
          className="hover:border-[var(--color-indigo)]/40 transition-all hover:shadow-sm"
        >
          <div className="p-4 sm:p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-[var(--color-ink)] text-base">
                    {ipo.company_name}
                  </p>
                  {ipo.status && (
                    <span
                      className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                        STATUS_STYLE[ipo.status] || STATUS_STYLE.Closed
                      }`}
                    >
                      {ipo.status}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {ipo.sector && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--color-line-soft)] text-[var(--color-ink-soft)] font-medium">
                      {ipo.sector}
                    </span>
                  )}
                  {ipo.document_type && (
                    <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] font-semibold">
                      {ipo.document_type}
                    </span>
                  )}
                  {ipo.filing_date && (
                    <span className="text-xs text-[var(--color-ink-faint)] font-mono">
                      Filed: {ipo.filing_date}
                    </span>
                  )}
                </div>

                {/* Financial Overview Chips */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2.5 text-xs text-[var(--color-ink-soft)]">
                  {ipo.issue_size && (
                    <span>
                      Issue: <strong className="text-[var(--color-ink)] font-semibold">{ipo.issue_size}</strong>
                    </span>
                  )}
                  {ipo.price_band && (
                    <span>
                      Band: <strong className="text-[var(--color-ink)] font-semibold">{ipo.price_band}</strong>
                    </span>
                  )}
                  {ipo.source_name && (
                    <span className="text-[var(--color-ink-faint)]">
                      Source: {ipo.source_name}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="mt-4 pt-3 border-t border-[var(--color-line-soft)] flex items-center justify-between gap-3">
              <div>
                {ipo.is_document_available ? (
                  <button
                    type="button"
                    onClick={() => onSelect(ipo)}
                    className="rounded-full bg-[var(--color-indigo)] text-white px-4 py-1.5 text-xs font-semibold
                      hover:bg-[var(--color-indigo-dark)] transition-colors focus-visible:outline focus-visible:outline-2
                      focus-visible:outline-offset-2 focus-visible:outline-[var(--color-indigo)] shadow-xs"
                  >
                    Select IPO →
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-[var(--color-ink-faint)]">
                      Prospectus unavailable for auto-retrieval
                    </span>
                    <button
                      type="button"
                      onClick={onUploadFallback}
                      className="text-xs text-[var(--color-indigo)] hover:underline font-semibold"
                    >
                      Upload DRHP
                    </button>
                  </div>
                )}
              </div>

              {ipo.source_url && (
                <a
                  href={ipo.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-[var(--color-ink-faint)] hover:text-[var(--color-indigo)] transition-colors inline-flex items-center gap-1"
                >
                  <span>Source</span>
                  <span>↗</span>
                </a>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
