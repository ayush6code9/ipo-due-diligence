import Card from '../common/Card'
import StatusBadge from '../common/StatusBadge'

export default function RiskCard({ category, severity, level, reason, impact }) {
  return (
    <Card className="flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-[var(--color-line-soft)]">
          <p className="font-semibold text-sm sm:text-base text-[var(--color-ink)]">{category}</p>
          <StatusBadge label={severity} level={level} size="sm" />
        </div>

        <div className="mt-3.5 space-y-3">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Identified Risk</p>
            <p className="text-xs sm:text-sm text-[var(--color-ink-soft)] mt-0.5 leading-relaxed">{reason}</p>
          </div>
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">
              Potential Business Impact
            </p>
            <p className="text-xs sm:text-sm text-[var(--color-ink-soft)] mt-0.5 leading-relaxed">{impact}</p>
          </div>
        </div>
      </div>
    </Card>
  )
}
