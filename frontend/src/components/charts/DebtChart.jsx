import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import ChartCard from './ChartCard'

export default function DebtChart({ data }) {
  return (
    <ChartCard title="Debt-to-Equity Trend" unit="ratio · lower is safer">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-line-soft)" vertical={false} />
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
            contentStyle={{
              backgroundColor: 'var(--color-paper-raised)',
              borderColor: 'var(--color-line)',
              color: 'var(--color-ink)',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
              fontSize: '12px',
              padding: '8px 12px',
            }}
            itemStyle={{ color: 'var(--color-signal-amber)', fontWeight: 600 }}
            labelStyle={{ color: 'var(--color-ink-faint)', fontSize: '11px', marginBottom: '2px' }}
            formatter={(value) => [value, 'Debt-to-Equity']}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--color-signal-amber)"
            strokeWidth={2.5}
            dot={{ r: 4, fill: 'var(--color-signal-amber)', strokeWidth: 0 }}
            activeDot={{ r: 6, fill: 'var(--color-signal-amber)' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
