import Card from '../common/Card'

const ROWS = [
  { key: 'retail', label: 'Retail Investors' },
  { key: 'nii', label: 'Non-Institutional (NII)' },
  { key: 'qib', label: 'Qualified Institutional (QIB)' },
  { key: 'overall', label: 'Total Subscription' },
]

function barWidth(multiple) {
  const capped = Math.min(multiple, 5)
  return `${(capped / 5) * 100}%`
}

export default function SubscriptionCard({ subscription }) {
  return (
    <Card className="flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Subscription Demand</p>
          <span className="text-xs font-mono text-[var(--color-ink-faint)]">
            {subscription.lastUpdated}
          </span>
        </div>

        <div className="mt-4 space-y-3.5">
          {ROWS.map(({ key, label }) => {
            const multiple = subscription[key]
            const hasData = multiple != null && Number.isFinite(multiple)
            const isFull = hasData && multiple >= 1
            return (
              <div key={key}>
                <div className="flex items-center justify-between text-xs sm:text-sm mb-1.5">
                  <span className="text-[var(--color-ink-soft)] font-medium">{label}</span>
                  <span
                    className={`font-display font-bold tabular-nums ${
                      isFull ? 'text-[var(--color-signal-green)]' : 'text-[var(--color-ink)]'
                    }`}
                  >
                    {hasData ? `${multiple.toFixed(2)}x` : '—'}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-[var(--color-line-soft)] overflow-hidden">
                  {hasData && (
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isFull ? 'bg-[var(--color-signal-green)]' : 'bg-[var(--color-indigo)]'
                      }`}
                      style={{ width: barWidth(multiple) }}
                    />
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <p className="text-[11px] text-[var(--color-ink-faint)] mt-4 pt-3 border-t border-[var(--color-line-soft)]">
        Subscription multiple (“x”) indicates total shares bid vs shares offered in that category.
      </p>
    </Card>
  )
}
