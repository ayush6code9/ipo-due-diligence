import { Link, useLocation } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

export default function Header() {
  const location = useLocation()
  const isSearchActive = location.pathname === '/get-started' && location.search.includes('mode=search')
  const isUploadActive = location.pathname === '/get-started' && location.search.includes('mode=upload')

  return (
    <header className="border-b border-[var(--color-line)] bg-[var(--color-paper)]/90 backdrop-blur-md sticky top-0 z-40 transition-colors">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <Link to="/" className="flex items-center gap-2.5 group shrink-0">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--color-indigo)] to-[var(--color-indigo-dark)] text-white font-display text-xs font-bold shadow-sm shadow-[var(--color-indigo)]/20 transition-transform group-hover:scale-105">
            IR
          </span>
          <div className="flex flex-col">
            <span className="font-display font-semibold text-[var(--color-ink)] text-base tracking-tight leading-tight">
              IPO Research
            </span>
            <span className="text-[10px] font-mono uppercase tracking-widest text-[var(--color-ink-faint)] leading-none hidden sm:inline">
              Platform
            </span>
          </div>
        </Link>

        {/* Navigation & Controls */}
        <div className="flex items-center gap-3 sm:gap-6">
          <nav className="flex items-center gap-1 sm:gap-2 text-sm">
            <Link
              to="/get-started?mode=search"
              className={`px-3 py-1.5 rounded-full font-medium transition-colors ${
                isSearchActive
                  ? 'bg-[var(--color-indigo-soft)] text-[var(--color-indigo)]'
                  : 'text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-line-soft)]'
              }`}
            >
              Search IPO
            </Link>
            <Link
              to="/get-started?mode=upload"
              className={`px-3 py-1.5 rounded-full font-medium transition-colors ${
                isUploadActive
                  ? 'bg-[var(--color-indigo-soft)] text-[var(--color-indigo)]'
                  : 'text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] hover:bg-[var(--color-line-soft)]'
              }`}
            >
              Upload DRHP
            </Link>
          </nav>

          <div className="h-4 w-px bg-[var(--color-line)]" />

          {/* Theme Toggle */}
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
