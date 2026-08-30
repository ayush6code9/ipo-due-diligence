export default function Card({ children, className = '', padded = true }) {
  return (
    <div
      className={`bg-[var(--color-paper-raised)] border border-[var(--color-line)] rounded-2xl shadow-xs transition-colors ${
        padded ? 'p-5 sm:p-6' : ''
      } ${className}`}
    >
      {children}
    </div>
  )
}
