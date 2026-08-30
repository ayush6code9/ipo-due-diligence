import { useNavigate } from 'react-router-dom'
import Button from '../common/Button'
import StatusBadge from '../common/StatusBadge'

export default function Hero() {
  const navigate = useNavigate()

  return (
    <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-12 sm:pt-20 pb-16">
      <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-12 lg:gap-14 items-center">
        {/* Left Column: Value Proposition */}
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] text-xs font-mono tracking-wider uppercase mb-5 border border-[var(--color-indigo)]/15">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-indigo)] animate-pulse" />
            Independent & Unbiased Analysis
          </div>

          <h1 className="font-display text-4xl sm:text-5xl lg:text-[3.25rem] font-bold text-[var(--color-ink)] leading-[1.1] tracking-tight">
            Research an IPO
            <br />
            <span className="text-[var(--color-indigo)]">before you invest.</span>
          </h1>

          <p className="mt-5 text-base sm:text-lg text-[var(--color-ink-soft)] max-w-xl leading-relaxed">
            Analyze IPO filings, financial health, risks, and promoter quality in one simple,
            investor-friendly platform.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button
              onClick={() => navigate('/get-started?mode=search')}
              className="px-6 py-3 text-sm font-semibold"
            >
              <span>Search IPO</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Button>
            <Button
              variant="secondary"
              onClick={() => navigate('/get-started?mode=upload')}
              className="px-6 py-3 text-sm font-semibold"
            >
              Upload DRHP
            </Button>
          </div>

          {/* Key Value Points */}
          <div className="mt-10 pt-8 border-t border-[var(--color-line)] grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Source</p>
              <p className="text-xs sm:text-sm font-medium text-[var(--color-ink)] mt-0.5">SEBI Filings</p>
            </div>
            <div>
              <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Language</p>
              <p className="text-xs sm:text-sm font-medium text-[var(--color-ink)] mt-0.5">Plain English</p>
            </div>
            <div>
              <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Speed</p>
              <p className="text-xs sm:text-sm font-medium text-[var(--color-ink)] mt-0.5">~2 Minutes</p>
            </div>
          </div>
        </div>

        {/* Right Column: Research Preview Card */}
        <div className="relative">
          <div className="absolute -inset-2 sm:-inset-3 rounded-3xl bg-gradient-to-tr from-[var(--color-indigo)]/10 via-transparent to-transparent -z-10 blur-sm" />
          <div className="bg-[var(--color-paper-raised)] border border-[var(--color-line)] rounded-2xl p-5 sm:p-6 shadow-sm shadow-[var(--color-ink)]/5 transition-colors">
            {/* Header / Meta */}
            <div className="flex items-center justify-between gap-2 pb-3 border-b border-[var(--color-line-soft)]">
              <div>
                <p className="font-mono text-[11px] font-medium tracking-wide text-[var(--color-indigo)] uppercase">
                  Research Snapshot
                </p>
                <p className="text-sm font-semibold text-[var(--color-ink)] mt-0.5">
                  Apex Industrial Components Ltd
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--color-line-soft)] text-[var(--color-ink-soft)] border border-[var(--color-line)]">
                DRHP Verified
              </span>
            </div>

            {/* Score & Health */}
            <div className="flex items-center justify-between mt-4">
              <div>
                <p className="text-xs text-[var(--color-ink-soft)]">Financial Health Score</p>
                <div className="flex items-baseline gap-1 mt-0.5">
                  <span className="font-display text-3xl sm:text-4xl font-bold text-[var(--color-signal-green)]">
                    84
                  </span>
                  <span className="text-sm text-[var(--color-ink-faint)] font-sans">/ 100</span>
                </div>
              </div>
              <StatusBadge label="Strong Financials" level="strong" size="sm" />
            </div>

            {/* Key Metrics Mini-Grid */}
            <div className="grid grid-cols-3 gap-2 mt-4 p-3 rounded-xl bg-[var(--color-line-soft)]/60 border border-[var(--color-line)]">
              <div>
                <p className="text-[10px] font-mono text-[var(--color-ink-faint)] uppercase">Rev Growth</p>
                <p className="font-display text-xs sm:text-sm font-semibold text-[var(--color-signal-green)] mt-0.5">
                  +18.4%
                </p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-[var(--color-ink-faint)] uppercase">Debt/Eq</p>
                <p className="font-display text-xs sm:text-sm font-semibold text-[var(--color-ink)] mt-0.5">
                  0.42x
                </p>
              </div>
              <div>
                <p className="text-[10px] font-mono text-[var(--color-ink-faint)] uppercase">Net Margin</p>
                <p className="font-display text-xs sm:text-sm font-semibold text-[var(--color-ink)] mt-0.5">
                  12.1%
                </p>
              </div>
            </div>

            {/* Insights Checklist */}
            <div className="h-px bg-[var(--color-line-soft)] my-4" />
            <ul className="space-y-2.5 text-xs sm:text-sm text-[var(--color-ink-soft)]">
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-signal-green)] font-bold shrink-0">✓</span>
                <span>Revenue has grown consistently across past 3 years</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-signal-green)] font-bold shrink-0">✓</span>
                <span>Debt level is under control with healthy interest cover</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-signal-amber)] font-bold shrink-0">⚠</span>
                <span>Customer concentration: top 3 clients account for 48% of sales</span>
              </li>
            </ul>

            {/* Card Footer */}
            <div className="mt-4 pt-3 border-t border-[var(--color-line-soft)] flex items-center justify-between text-[11px] text-[var(--color-ink-faint)]">
              <span>Automated Prospectus Ingestion</span>
              <span className="text-[var(--color-indigo)] font-medium">Full Analysis Ready →</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
