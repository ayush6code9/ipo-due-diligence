import Card from '../common/Card'
import ScoreStamp from '../common/ScoreStamp'
import StatusBadge from '../common/StatusBadge'

export default function FinancialHealthCard({ health }) {
  return (
    <Card>
      <div className="flex flex-col sm:flex-row sm:items-center gap-6">
        <ScoreStamp score={health.score} maxScore={health.maxScore} level={health.level} />
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Financial Health Summary</p>
          <div className="mt-1.5 flex items-center gap-2">
            <StatusBadge label={health.status} level={health.level} />
          </div>
          <p className="text-xs text-[var(--color-ink-soft)] mt-2 max-w-md">
            Calculated objectively from revenue trends, debt ratios, profit margins, and return metrics.
          </p>
        </div>
      </div>

      <div className="mt-6 pt-5 border-t border-[var(--color-line-soft)]">
        <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)] mb-3">Key Factors Driving Score</p>
        <ul className="space-y-2.5">
          {health.reasons.map((reason) => (
            <li key={reason} className="flex items-start gap-2.5 text-sm text-[var(--color-ink-soft)]">
              <span className="text-[var(--color-signal-green)] font-bold shrink-0 mt-0.5">✓</span>
              <span className="leading-relaxed">{reason}</span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  )
}
