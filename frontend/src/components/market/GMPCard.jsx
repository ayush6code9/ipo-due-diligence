import Card from '../common/Card'

export default function GMPCard({ gmp }) {
  return (
    <Card className="flex flex-col justify-between">
      <div>
        <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Grey Market Premium (GMP)</p>
        <div className="flex items-baseline gap-2 mt-2">
          <p className="font-display text-3xl font-bold text-[var(--color-ink)] tabular-nums">
            {gmp.value}
          </p>
          {gmp.percentOfCap && gmp.percentOfCap !== '—' && (
            <span className="text-sm font-semibold text-[var(--color-signal-green)]">
              ({gmp.percentOfCap} over cap)
            </span>
          )}
        </div>
        <p className="text-xs font-mono text-[var(--color-ink-faint)] mt-2">
          Last updated: {gmp.lastUpdated}
        </p>
      </div>

      <div className="mt-5 flex items-start gap-2.5 rounded-xl bg-[var(--color-signal-amber-soft)] border border-[var(--color-signal-amber)]/20 p-3">
        <span className="text-[var(--color-signal-amber)] text-xs font-bold shrink-0 mt-0.5">ⓘ</span>
        <p className="text-xs text-[var(--color-signal-amber)] leading-relaxed">{gmp.note}</p>
      </div>
    </Card>
  )
}
