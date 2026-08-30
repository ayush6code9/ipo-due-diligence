import Card from '../common/Card'
import LearnMore from '../common/LearnMore'

const TREND_GLYPH = { up: '↑', down: '↓', flat: '→' }
const TREND_COLOR = {
  up: 'text-[var(--color-signal-green)] bg-[var(--color-signal-green-soft)] border-[var(--color-signal-green)]/20',
  down: 'text-[var(--color-signal-red)] bg-[var(--color-signal-red-soft)] border-[var(--color-signal-red)]/20',
  flat: 'text-[var(--color-ink-faint)] bg-[var(--color-line-soft)] border-[var(--color-line)]',
}

export default function MetricCard({ label, value, trend, meaning, learnMore }) {
  return (
    <Card className="h-full flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">{label}</p>
          {trend && (
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-md border ${TREND_COLOR[trend]}`}
              aria-hidden="true"
            >
              {TREND_GLYPH[trend]} {trend.toUpperCase()}
            </span>
          )}
        </div>

        <p className="font-display text-2xl sm:text-3xl font-bold text-[var(--color-ink)] mt-2 tabular-nums">
          {value}
        </p>

        <div className="mt-4 flex items-center gap-2" aria-hidden="true">
          <span className="text-[var(--color-ink-faint)] text-[11px] font-mono">↳ Interpretation</span>
          <span className="h-px flex-1 bg-[var(--color-line)]" />
        </div>

        <p className="mt-2 text-xs sm:text-sm text-[var(--color-ink-soft)] leading-relaxed">
          {meaning}
        </p>
      </div>

      {learnMore && (
        <div className="mt-4 pt-3 border-t border-[var(--color-line-soft)]">
          <LearnMore>{learnMore}</LearnMore>
        </div>
      )}
    </Card>
  )
}
