interface SkeletonProps {
  variant?: 'text' | 'heading' | 'chart' | 'card';
  width?: string;
  height?: string;
  count?: number;
}

export function Skeleton({ variant = 'text', width, height, count = 1 }: SkeletonProps) {
  const className = `skeleton skeleton-${variant}`;
  const style = { width, height };

  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={className} style={style} role="status" aria-label="Loading..." />
      ))}
    </>
  );
}

export function CardSkeleton() {
  return (
    <div className="card">
      <div className="card-header">
        <Skeleton variant="text" width="40%" />
      </div>
      <div className="card-body">
        <Skeleton variant="chart" />
      </div>
    </div>
  );
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-4">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="card stat-card">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="heading" width="40%" />
        </div>
      ))}
    </div>
  );
}
