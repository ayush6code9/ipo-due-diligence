export default function Footer() {
  return (
    <footer className="border-t border-[var(--color-line)] mt-20 transition-colors bg-[var(--color-paper)]">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-10">
        <div className="flex flex-col sm:flex-row items-start justify-between gap-6">
          <div className="max-w-2xl">
            <p className="text-xs text-[var(--color-ink-faint)] leading-relaxed">
              This platform is designed to assist retail investors in researching and understanding official IPO filings.
              It does not provide investment advice, recommendations, or guarantees of performance. Scores, risk indicators,
              GMP metrics, and subscription numbers are for educational analysis only. Always read the complete Draft Red Herring Prospectus (DRHP)
              and consult a SEBI-registered financial advisor before making investment decisions.
            </p>
          </div>
          <div className="text-xs text-[var(--color-ink-faint)] shrink-0 font-mono">
            IPO Research Platform
          </div>
        </div>
      </div>
    </footer>
  )
}
