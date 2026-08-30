const VARIANTS = {
  primary:
    'bg-[var(--color-indigo)] text-white hover:bg-[var(--color-indigo-dark)] shadow-sm shadow-[var(--color-indigo)]/20 border border-transparent active:scale-[0.98]',
  secondary:
    'bg-[var(--color-paper-raised)] text-[var(--color-ink)] border border-[var(--color-line)] hover:border-[var(--color-ink-faint)] hover:bg-[var(--color-line-soft)] active:scale-[0.98]',
  ghost:
    'bg-transparent text-[var(--color-indigo)] border border-transparent hover:bg-[var(--color-indigo-soft)] active:scale-[0.98]',
}

export default function Button({
  children,
  variant = 'primary',
  className = '',
  disabled = false,
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium
        transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2
        focus-visible:outline-[var(--color-indigo)] disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none
        ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
