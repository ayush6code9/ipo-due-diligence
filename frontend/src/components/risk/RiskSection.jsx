import RiskCard from './RiskCard'

export default function RiskSection({ risks }) {
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      {risks.map((risk) => (
        <RiskCard key={risk.category} {...risk} />
      ))}
    </div>
  )
}
