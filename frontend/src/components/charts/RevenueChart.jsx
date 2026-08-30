import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import ChartCard from './ChartCard'

export default function RevenueChart({ data }) {
  return (
    <ChartCard title="Historical Revenue" unit="₹ Crore">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <XAxis
            dataKey="year"
            tick={{ fontSize: 11, fill: 'var(--color-ink-faint)', fontFamily: 'var(--font-mono)' }}
            axisLine={{ stroke: 'var(--color-line)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--color-ink-faint)', fontFamily: 'var(--font-mono)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: 'var(--color-indigo-soft)', opacity: 0.5 }}
            contentStyle={{
              backgroundColor: 'var(--color-paper-raised)',
              borderColor: 'var(--color-line)',
              color: 'var(--color-ink)',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              fontSize: '12px',
              padding: '8px 12px',
            }}
            itemStyle={{ color: 'var(--color-indigo)', fontWeight: 600 }}
            labelStyle={{ color: 'var(--color-ink-faint)', fontSize: '11px', marginBottom: '2px' }}
            formatter={(value) => [`₹${value} Cr`, 'Revenue']}
          />
          <Bar dataKey="value" fill="var(--color-indigo)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
