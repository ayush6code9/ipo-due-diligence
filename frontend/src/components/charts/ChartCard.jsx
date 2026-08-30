import Card from '../common/Card'

export default function ChartCard({ title, unit, children }) {
  return (
    <Card className="flex flex-col justify-between">
      <div className="flex items-baseline justify-between mb-3 pb-2 border-b border-[var(--color-line-soft)]">
        <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink)] font-semibold">{title}</p>
        {unit && <p className="text-[11px] font-mono text-[var(--color-ink-faint)]">{unit}</p>}
      </div>
      <div className="h-52 w-full pt-2">{children}</div>
    </Card>
  )
}
