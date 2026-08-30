import Card from '../common/Card'
import StarRating from '../common/StarRating'
import StatusBadge from '../common/StatusBadge'

export default function PromoterQualityCard({ promoter }) {
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <StarRating stars={promoter.stars} maxStars={promoter.maxStars} />
        <StatusBadge label={promoter.label} level={promoter.level} />
      </div>

      <div className="mt-5 pt-5 border-t border-[var(--color-line-soft)]">
        <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)] mb-3">Key Promoter Observations</p>
        <ul className="space-y-2.5">
          {promoter.points.map((point) => (
            <li key={point} className="flex items-start gap-2 text-sm text-[var(--color-ink-soft)]">
              <span className="text-[var(--color-signal-green)] font-bold shrink-0 mt-0.5">✓</span>
              <span className="leading-relaxed">{point}</span>
            </li>
          ))}
        </ul>

        {promoter.litigation?.present && (
          <div className="mt-4 flex items-start gap-2.5 rounded-xl bg-[var(--color-signal-amber-soft)] border border-[var(--color-signal-amber)]/20 p-3.5">
            <span className="text-[var(--color-signal-amber)] font-bold shrink-0 mt-0.5">⚠</span>
            <p className="text-xs sm:text-sm text-[var(--color-signal-amber)] leading-relaxed">
              {promoter.litigation.note}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}
