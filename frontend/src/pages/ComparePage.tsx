import { useEffect, useState } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import { Alert } from '../components/common/Alert';
import { CardSkeleton } from '../components/common/Skeleton';
import type { ComparisonResult, FilterParams } from '../types';
import { api } from '../services/api';
import { ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function ComparePage() {
  const { jobs, currentResult, activeJobId, loadJobs, selectJob } = useAnalysis();
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [segmentA, setSegmentA] = useState<FilterParams>({});
  const [segmentB, setSegmentB] = useState<FilterParams>({});

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    if (jobs.length > 0 && !activeJobId) {
      const completed = jobs.find((j) => j.status === 'completed');
      if (completed) selectJob(completed.job_id);
    }
  }, [jobs, activeJobId, selectJob]);

  const handleCompare = async () => {
    if (!currentResult) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.compareSegments(currentResult.job_id, segmentA, segmentB);
      setComparison(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  if (!currentResult) {
    return (
      <div>
        <div className="page-header">
          <h2>Compare Segments</h2>
          <p>Upload and analyze data first to compare segments.</p>
        </div>
      </div>
    );
  }

  const DeltaIcon = comparison
    ? comparison.sentiment_delta > 0.01
      ? TrendingUp
      : comparison.sentiment_delta < -0.01
        ? TrendingDown
        : Minus
    : Minus;

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Compare Segments</h2>
          <p>Compare sentiment and topics between two time periods or data segments</p>
        </div>
        {jobs.filter((j) => j.status === 'completed').length > 1 && (
          <select
            className="select"
            value={activeJobId || ''}
            onChange={(e) => {
              selectJob(e.target.value);
              setComparison(null);
            }}
            aria-label="Select analysis job"
          >
            {jobs
              .filter((j) => j.status === 'completed')
              .map((j) => (
                <option key={j.job_id} value={j.job_id}>
                  {j.job_id} — {new Date(j.created_at).toLocaleDateString()}
                </option>
              ))}
          </select>
        )}
      </div>

      {error && <Alert type="danger" message={error} onDismiss={() => setError(null)} />}

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header">
            <h3>Segment A</h3>
          </div>
          <div className="card-body">
            <div className="filter-group mb-4">
              <label className="label" htmlFor="seg-a-from">Date From</label>
              <input
                id="seg-a-from"
                type="date"
                className="input"
                onChange={(e) => setSegmentA({ ...segmentA, date_from: e.target.value + 'T00:00:00' })}
              />
            </div>
            <div className="filter-group">
              <label className="label" htmlFor="seg-a-to">Date To</label>
              <input
                id="seg-a-to"
                type="date"
                className="input"
                onChange={(e) => setSegmentA({ ...segmentA, date_to: e.target.value + 'T23:59:59' })}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Segment B</h3>
          </div>
          <div className="card-body">
            <div className="filter-group mb-4">
              <label className="label" htmlFor="seg-b-from">Date From</label>
              <input
                id="seg-b-from"
                type="date"
                className="input"
                onChange={(e) => setSegmentB({ ...segmentB, date_from: e.target.value + 'T00:00:00' })}
              />
            </div>
            <div className="filter-group">
              <label className="label" htmlFor="seg-b-to">Date To</label>
              <input
                id="seg-b-to"
                type="date"
                className="input"
                onChange={(e) => setSegmentB({ ...segmentB, date_to: e.target.value + 'T23:59:59' })}
              />
            </div>
          </div>
        </div>
      </div>

      <button className="btn btn-primary mb-4" onClick={handleCompare} disabled={loading}>
        {loading ? 'Comparing…' : 'Compare Segments'}
        <ArrowRight size={14} />
      </button>

      {loading && <CardSkeleton />}

      {comparison && (
        <div>
          <div className="grid grid-3 mb-4">
            <div className="card stat-card">
              <div className="stat-label">Segment A — Avg Sentiment</div>
              <div className="stat-value">{comparison.segment_a.avg_sentiment.toFixed(3)}</div>
              <span className={`badge badge-${comparison.segment_a.dominant_sentiment}`}>
                {comparison.segment_a.dominant_sentiment}
              </span>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {comparison.segment_a.total_entries} entries • {comparison.segment_a.num_topics} topics
              </div>
            </div>

            <div className="card stat-card" style={{ textAlign: 'center' }}>
              <div className="stat-label">Sentiment Delta</div>
              <div className="stat-value flex items-center justify-between" style={{ justifyContent: 'center', gap: 8 }}>
                <DeltaIcon
                  size={24}
                  style={{
                    color: comparison.sentiment_delta > 0 ? 'var(--success)' : comparison.sentiment_delta < 0 ? 'var(--danger)' : 'var(--text-muted)',
                  }}
                />
                <span
                  style={{
                    color: comparison.sentiment_delta > 0 ? 'var(--success)' : comparison.sentiment_delta < 0 ? 'var(--danger)' : 'var(--text-primary)',
                  }}
                >
                  {comparison.sentiment_delta > 0 ? '+' : ''}
                  {comparison.sentiment_delta.toFixed(3)}
                </span>
              </div>
            </div>

            <div className="card stat-card">
              <div className="stat-label">Segment B — Avg Sentiment</div>
              <div className="stat-value">{comparison.segment_b.avg_sentiment.toFixed(3)}</div>
              <span className={`badge badge-${comparison.segment_b.dominant_sentiment}`}>
                {comparison.segment_b.dominant_sentiment}
              </span>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {comparison.segment_b.total_entries} entries • {comparison.segment_b.num_topics} topics
              </div>
            </div>
          </div>

          {comparison.new_topics.length > 0 && (
            <div className="card mb-4">
              <div className="card-header">
                <h3>New Topics in Segment B</h3>
              </div>
              <div className="card-body flex gap-2" style={{ flexWrap: 'wrap' }}>
                {comparison.new_topics.map((t) => (
                  <span key={t.topic_id} className="badge badge-positive">{t.label}</span>
                ))}
              </div>
            </div>
          )}

          {comparison.disappeared_topics.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3>Topics No Longer in Segment B</h3>
              </div>
              <div className="card-body flex gap-2" style={{ flexWrap: 'wrap' }}>
                {comparison.disappeared_topics.map((t) => (
                  <span key={t.topic_id} className="badge badge-negative">{t.label}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
