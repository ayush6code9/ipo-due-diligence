export default function SectionHeading({ index, title, subtitle, id }) {
  return (
    <div id={id} className="scroll-mt-24 mb-5">
      {index != null && (
        <p className="font-mono text-[11px] font-semibold tracking-wider text-[var(--color-indigo)] uppercase mb-1">
          {String(index).padStart(2, '0')} · Section
        </p>
      )}
      <h2 className="font-display text-xl sm:text-2xl font-bold text-[var(--color-ink)] tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="text-xs sm:text-sm text-[var(--color-ink-soft)] mt-1 max-w-2xl leading-relaxed">{subtitle}</p>
      )}
    </div>
  )
}
