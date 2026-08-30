import Card from '../common/Card'

export default function TopStrengthsRisks({ strengths = [], risks = [] }) {
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      <Card>
        <div className="flex items-center gap-2 mb-3.5 pb-2.5 border-b border-[var(--color-line-soft)]">
          <span className="text-[var(--color-signal-green)] font-bold text-sm">✓</span>
          <p className="text-sm font-semibold text-[var(--color-ink)]">Key Strengths</p>
        </div>
        <ul className="space-y-3">
          {strengths.map((s) => (
            <li key={s} className="flex items-start gap-2.5 text-xs sm:text-sm text-[var(--color-ink-soft)] leading-relaxed">
              <span className="text-[var(--color-signal-green)] font-bold shrink-0 mt-0.5">•</span>
              <span>{s}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <div className="flex items-center gap-2 mb-3.5 pb-2.5 border-b border-[var(--color-line-soft)]">
          <span className="text-[var(--color-signal-amber)] font-bold text-sm">⚠</span>
          <p className="text-sm font-semibold text-[var(--color-ink)]">Key Watchpoints & Risks</p>
        </div>
        <ul className="space-y-3">
          {risks.map((r) => (
            <li key={r} className="flex items-start gap-2.5 text-xs sm:text-sm text-[var(--color-ink-soft)] leading-relaxed">
              <span className="text-[var(--color-signal-amber)] font-bold shrink-0 mt-0.5">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
