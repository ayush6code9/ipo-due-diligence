import MetricCard from './MetricCard'

export default function FinancialMetricsGrid({ metrics }) {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {metrics.map(({ key, ...metric }) => (
        <MetricCard key={key} {...metric} />
      ))}
    </div>
  )
}
