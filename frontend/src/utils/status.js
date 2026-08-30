// Single source of truth for status colors across the dashboard.
// `level` is one of: 'strong' | 'moderate' | 'high-risk'
// Keeping this in one place means a risk badge, a score ring, and a
// metric arrow all agree on what "medium risk" looks like.

export const STATUS = {
  strong: {
    text: 'text-[var(--color-signal-green)]',
    bg: 'bg-[var(--color-signal-green-soft)]',
    border: 'border-[var(--color-signal-green)]/25',
    dot: 'bg-[var(--color-signal-green)]',
  },
  moderate: {
    text: 'text-[var(--color-signal-amber)]',
    bg: 'bg-[var(--color-signal-amber-soft)]',
    border: 'border-[var(--color-signal-amber)]/25',
    dot: 'bg-[var(--color-signal-amber)]',
  },
  'high-risk': {
    text: 'text-[var(--color-signal-red)]',
    bg: 'bg-[var(--color-signal-red-soft)]',
    border: 'border-[var(--color-signal-red)]/25',
    dot: 'bg-[var(--color-signal-red)]',
  },
}

export function statusFor(level) {
  return STATUS[level] || STATUS.moderate
}

// Maps a severity label ("Low" / "Medium" / "High") to the same level keys.
export function levelForSeverity(severity) {
  const s = (severity || '').toLowerCase()
  if (s === 'low') return 'strong'
  if (s === 'high') return 'high-risk'
  return 'moderate'
}
