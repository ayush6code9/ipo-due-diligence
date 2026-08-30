import RevenueChart from './RevenueChart'
import ProfitChart from './ProfitChart'
import DebtChart from './DebtChart'

export default function ChartsSection({ charts }) {
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <RevenueChart data={charts.revenue} />
      <ProfitChart data={charts.profit} />
      <DebtChart data={charts.debt} />
    </div>
  )
}
