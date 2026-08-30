import { useEffect, useState } from 'react'

const SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'ipo-parameters', label: 'IPO Parameters' },
  { id: 'market-data', label: 'GMP & Subscription' },
  { id: 'financial-health', label: 'Financial Health' },
  { id: 'financial-metrics', label: 'Financial Metrics' },
  { id: 'risk-analysis', label: 'Risk Analysis' },
  { id: 'promoter-quality', label: 'Promoter Quality' },
  { id: 'strengths-risks', label: 'Strengths & Risks' },
  { id: 'charts', label: 'Charts' },
  { id: 'ai-summary', label: 'AI Summary' },
  { id: 'chat', label: 'Chat with DRHP' },
  { id: 'download-report', label: 'Download Report' },
]

export default function DashboardNav() {
  const [activeId, setActiveId] = useState(SECTIONS[0].id)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveId(entry.target.id)
        })
      },
      { rootMargin: '-15% 0px -70% 0px' }
    )
    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    })
    return () => observer.disconnect()
  }, [])

  return (
    <nav className="hidden lg:block sticky top-24 self-start w-52 shrink-0 pr-4">
      <p className="font-mono text-[11px] font-semibold tracking-wider text-[var(--color-ink-faint)] uppercase mb-3 px-3">
        Contents
      </p>
      <ul className="space-y-0.5 border-l border-[var(--color-line)] transition-colors">
        {SECTIONS.map((s) => (
          <li key={s.id}>
            <a
              href={`#${s.id}`}
              className={`block pl-3 -ml-px border-l-2 py-1.5 text-xs font-medium transition-all ${
                activeId === s.id
                  ? 'border-[var(--color-indigo)] text-[var(--color-indigo)] bg-[var(--color-indigo-soft)]/50 rounded-r-md font-semibold'
                  : 'border-transparent text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:border-[var(--color-line)]'
              }`}
            >
              {s.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
