export default function SearchBar({ value, onChange, onSubmit, loading }) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit?.()
      }}
      className="flex flex-col sm:flex-row gap-3"
    >
      <div className="relative flex-1">
        {/* Search Icon */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-ink-faint)] pointer-events-none">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter company or IPO name (e.g. Apex, Tempsens, Tata)"
          className="w-full rounded-full border border-[var(--color-line)] bg-[var(--color-paper-raised)]
            pl-11 pr-10 py-3 text-sm text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)]
            focus:outline-none focus:ring-2 focus:ring-[var(--color-indigo)]/40 focus:border-[var(--color-indigo)]
            shadow-xs transition-all"
        />

        {loading && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center">
            <span className="h-4 w-4 rounded-full border-2 border-[var(--color-indigo)] border-t-transparent animate-spin" />
          </div>
        )}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-[var(--color-indigo)] text-white px-6 py-3 text-sm font-semibold
          hover:bg-[var(--color-indigo-dark)] shadow-sm shadow-[var(--color-indigo)]/20 transition-all focus-visible:outline focus-visible:outline-2
          focus-visible:outline-offset-2 focus-visible:outline-[var(--color-indigo)] disabled:opacity-70 active:scale-[0.98]"
      >
        Search
      </button>
    </form>
  )
}
