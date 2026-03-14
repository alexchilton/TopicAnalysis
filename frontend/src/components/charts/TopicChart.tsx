import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { TopicCluster } from '../../types';

interface TopicBarChartProps {
  topics: TopicCluster[];
  height?: number;
}

const COLORS = [
  '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
  '#f43f5e', '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#06b6d4', '#3b82f6',
];

export function TopicBarChart({ topics, height = 300 }: TopicBarChartProps) {
  const data = topics
    .filter((t) => t.topic_id !== -1)
    .sort((a, b) => b.size - a.size)
    .slice(0, 15)
    .map((t) => ({
      name: t.label.length > 25 ? t.label.slice(0, 25) + '…' : t.label,
      size: t.size,
      sentiment: t.avg_sentiment,
      topic_id: t.topic_id,
    }));

  if (!data.length) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No topics found
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 120 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
        <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11, fill: 'var(--text-secondary)' }}
          width={110}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            fontSize: 12,
          }}
          formatter={(value: number, name: string) => {
            if (name === 'size') return [value, 'Entries'];
            return [value.toFixed(3), 'Avg Sentiment'];
          }}
        />
        <Bar dataKey="size" radius={[0, 4, 4, 0]} maxBarSize={24}>
          {data.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]!} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
