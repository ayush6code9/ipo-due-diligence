import GMPCard from './GMPCard'
import SubscriptionCard from './SubscriptionCard'

export default function MarketDataSection({ gmp, subscription }) {
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      <GMPCard gmp={gmp} />
      <SubscriptionCard subscription={subscription} />
    </div>
  )
}
