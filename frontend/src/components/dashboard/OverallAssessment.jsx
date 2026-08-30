import Card from '../common/Card'
import ScoreStamp from '../common/ScoreStamp'
import StatusBadge from '../common/StatusBadge'

function MiniStat({ label, value, level }) {
  return (
    <div className="p-3.5 rounded-xl bg-[var(--color-line-soft)]/50 border border-[var(--color-line)]">
      <p className="text-[11px] font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">{label}</p>
      <div className="mt-1.5">
        <StatusBadge label={value} level={level} size="sm" />
      </div>
    </div>
  )
}

export default function OverallAssessment({ ipo }) {
  const { overallAssessment, riskLevel, promoterQuality, marketInterest } = ipo

  return (
    <Card className="bg-[var(--color-paper-raised)]">
      <div className="flex flex-col sm:flex-row sm:items-center gap-6 sm:gap-8">
        <div className="flex items-center gap-5 shrink-0">
          <ScoreStamp
            score={overallAssessment.score}
            maxScore={overallAssessment.maxScore}
            level={overallAssessment.level}
          />
          <div>
            <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Overall Assessment</p>
            <p className="font-display text-xl sm:text-2xl font-bold text-[var(--color-ink)] mt-0.5">
              {overallAssessment.label}
            </p>
          </div>
        </div>

        <div className="h-px sm:h-20 sm:w-px w-full bg-[var(--color-line)] shrink-0" />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1">
          <MiniStat label="Risk Level" value={riskLevel.label} level={riskLevel.level} />
          <MiniStat
            label="Promoter Quality"
            value={promoterQuality.label}
            level={promoterQuality.level}
          />
          <MiniStat label="Market Interest" value={marketInterest.label} level={marketInterest.level} />
        </div>
      </div>
    </Card>
  )
}
