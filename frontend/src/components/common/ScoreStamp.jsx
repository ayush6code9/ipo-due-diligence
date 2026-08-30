import { statusFor } from '../../utils/status'

// The "assessment stamp": a double-ring numeric score, evoking an official
// document stamp rather than a generic circular progress ring. Used prominently
// for the Overall Assessment.
export default function ScoreStamp({ score, maxScore = 100, level, size = 'lg' }) {
  const s = statusFor(level)
  const dimensions = size === 'lg' ? 'h-32 w-32' : 'h-20 w-20'
  const scoreText = size === 'lg' ? 'text-4xl' : 'text-2xl'

  return (
    <div
      className={`relative shrink-0 flex flex-col items-center justify-center rounded-full border-2 ${s.border} ${dimensions} bg-[var(--color-paper-raised)] transition-all`}
      style={{ boxShadow: `inset 0 0 0 3px var(--color-paper-raised), inset 0 0 0 5px currentColor` }}
    >
      <div className={`absolute inset-1.5 rounded-full border ${s.border}`} />
      <span className={`font-display font-bold ${scoreText} ${s.text} tabular-nums leading-none`}>
        {score}
      </span>
      <span className="text-[10px] font-mono tracking-wider text-[var(--color-ink-faint)] uppercase mt-1">
        of {maxScore}
      </span>
    </div>
  )
}
