import { Link } from 'react-router-dom'

export default function DashboardHeader({ ipo }) {
  return (
    <div className="mb-10 pb-8 border-b border-[var(--color-line)] transition-colors">
      <Link
        to="/get-started"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--color-indigo)] hover:text-[var(--color-indigo-dark)] transition-colors mb-3"
      >
        ← Analyse another IPO
      </Link>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-display text-2xl sm:text-3xl lg:text-4xl font-bold text-[var(--color-ink)] tracking-tight">
              {ipo.companyName}
            </h1>
            {ipo.sector && (
              <span className="text-xs font-mono font-medium px-2.5 py-1 rounded-md bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] border border-[var(--color-indigo)]/15">
                {ipo.sector}
              </span>
            )}
          </div>
        </div>
      </div>
      {ipo.overview && (
        <p className="text-sm text-[var(--color-ink-soft)] mt-3 max-w-3xl leading-relaxed">
          {ipo.overview}
        </p>
      )}
    </div>
  )
}
