import Card from '../common/Card'

export default function IPOParametersCard({ params = {} }) {
  const rows = [
    { label: 'Issue Size', value: params.issueSize || params.issue_size || '—' },
    { label: 'Price Band', value: params.priceBand || params.price_band || '—' },
    { label: 'Lot Size', value: params.lotSize || params.lot_size || '—' },
    { label: 'Minimum Investment', value: params.minInvestment || params.minimum_investment || '—' },
    { label: 'Fresh Issue', value: params.freshIssue || params.fresh_issue || '—' },
    { label: 'Offer for Sale (OFS)', value: params.offerForSale || params.offer_for_sale || '—' },
    { label: 'Issue Opens', value: params.openDate || params.ipo_open_date || '—' },
    { label: 'Issue Closes', value: params.closeDate || params.ipo_close_date || '—' },
  ]

  return (
    <Card>
      <div className="flex items-center justify-between mb-5">
        <p className="text-xs font-mono uppercase tracking-wider text-[var(--color-ink-faint)]">Key Offering Terms</p>
        <span className="text-[11px] font-mono text-[var(--color-ink-faint)]">Official DRHP Data</span>
      </div>

      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {rows.map((row) => (
          <div key={row.label} className="p-3 rounded-xl bg-[var(--color-line-soft)]/50 border border-[var(--color-line)]">
            <dt className="text-[11px] font-medium text-[var(--color-ink-faint)] truncate">{row.label}</dt>
            <dd className="font-display text-sm sm:text-base font-semibold text-[var(--color-ink)] mt-1 tabular-nums">
              {row.value}
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  )
}
