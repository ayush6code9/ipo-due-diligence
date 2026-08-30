import { statusFor } from '../../utils/status'

export default function StatusBadge({ label, level, size = 'md' }) {
  const s = statusFor(level)
  const sizeClasses = size === 'sm' ? 'text-xs px-2.5 py-0.5' : 'text-xs sm:text-sm px-3 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${s.bg} ${s.text} ${s.border} ${sizeClasses} transition-colors`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot} shrink-0`} aria-hidden="true" />
      {label}
    </span>
  )
}
