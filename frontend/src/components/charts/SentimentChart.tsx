import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  Legend,
} from 'recharts';
import type { SentimentTrend } from '../../types';

interface SentimentChartProps {
  data: SentimentTrend[];
  height?: number;
}

export function SentimentTrendChart({ data, height = 300 }: SentimentChartProps) {
  if (!data.length) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No trend data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <defs>
          <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
            <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="ciGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="var(--info)" stopOpacity={0.1} />
            <stop offset="95%" stopColor="var(--info)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(value: number) => [value.toFixed(3), '']}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="confidence_upper"
          stroke="none"
          fill="url(#ciGradient)"
          name="CI Upper"
        />
        <Area
          type="monotone"
          dataKey="confidence_lower"
          stroke="none"
          fill="transparent"
          name="CI Lower"
        />
        <Area
          type="monotone"
          dataKey="avg_sentiment"
          stroke="var(--accent)"
          fill="url(#sentimentGradient)"
          strokeWidth={2}
          name="Avg Sentiment"
          dot={{ r: 3, fill: 'var(--accent)' }}
          activeDot={{ r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface SentimentDistributionProps {
  positive: number;
  negative: number;
  neutral: number;
}

export function SentimentDistribution({ positive, negative, neutral }: SentimentDistributionProps) {
  const total = positive + negative + neutral || 1;

  return (
    <div style={{ display: 'flex', gap: 4, height: 8, borderRadius: 4, overflow: 'hidden' }}>
      <div
        style={{
          width: `${(positive / total) * 100}%`,
          background: 'var(--success)',
          borderRadius: '4px 0 0 4px',
        }}
        title={`Positive: ${positive}`}
      />
      <div
        style={{
          width: `${(neutral / total) * 100}%`,
          background: 'var(--text-muted)',
        }}
        title={`Neutral: ${neutral}`}
      />
      <div
        style={{
          width: `${(negative / total) * 100}%`,
          background: 'var(--danger)',
          borderRadius: '0 4px 4px 0',
        }}
        title={`Negative: ${negative}`}
      />
    </div>
  );
}
