import Card from '../common/Card'

export default function AISummaryCard({ summary }) {
  return (
    <Card className="bg-[var(--color-indigo-soft)]/50 border-[var(--color-indigo)]/20 shadow-xs">
      <div className="flex items-center gap-2 mb-3">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--color-indigo)] text-white text-[10px] font-bold">
          ✦
        </span>
        <p className="font-display text-base font-semibold text-[var(--color-ink)]">
          Executive IPO Summary
        </p>
      </div>

      <p className="text-sm text-[var(--color-ink-soft)] leading-relaxed italic">
        “{summary}”
      </p>

      <p className="text-[11px] text-[var(--color-ink-faint)] mt-4 pt-3 border-t border-[var(--color-indigo)]/15">
        Synthesized deterministically from the parsed DRHP figures and extracted metrics above — for research and evaluation purposes only.
      </p>
    </Card>
  )
}
