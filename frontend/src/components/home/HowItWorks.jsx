const steps = [
  {
    n: '01',
    title: 'Search or upload',
    body: 'Find an IPO or upload its DRHP to begin your research.',
  },
  {
    n: '02',
    title: 'We analyze the filing',
    body: 'The platform extracts key financials, risks, and promoter information.',
  },
  {
    n: '03',
    title: 'Understand the results',
    body: 'Get a clear, plain-English view of financial health, risks, and key findings.',
  },
]

export default function HowItWorks() {
  return (
    <section className="border-t border-[var(--color-line)] bg-[var(--color-paper-raised)]/50 transition-colors">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-16">
        <div className="text-center max-w-xl mx-auto mb-12">
          <p className="font-mono text-xs text-[var(--color-indigo)] tracking-widest uppercase">
            Simple 3-Step Process
          </p>
          <h2 className="font-display text-2xl sm:text-3xl font-semibold text-[var(--color-ink)] mt-2">
            How IPO Research Works
          </h2>
        </div>

        <div className="grid sm:grid-cols-3 gap-6 sm:gap-8">
          {steps.map((step) => (
            <div
              key={step.n}
              className="p-6 rounded-2xl bg-[var(--color-paper-raised)] border border-[var(--color-line)] shadow-xs transition-colors hover:border-[var(--color-indigo)]/30"
            >
              <span className="inline-block font-mono text-xs font-semibold text-[var(--color-indigo)] bg-[var(--color-indigo-soft)] px-2.5 py-1 rounded-md border border-[var(--color-indigo)]/15">
                {step.n}
              </span>
              <h3 className="font-display text-lg font-semibold text-[var(--color-ink)] mt-4">
                {step.title}
              </h3>
              <p className="text-sm text-[var(--color-ink-soft)] mt-2 leading-relaxed">
                {step.body}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
