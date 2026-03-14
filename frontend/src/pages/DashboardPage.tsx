import { useState, useEffect, useCallback } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import { SentimentTrendChart, SentimentDistribution } from '../components/charts/SentimentChart';
import { TopicBarChart } from '../components/charts/TopicChart';
import { ForceGraph } from '../components/graphs/ForceGraph';
import { FilterBar } from '../components/filters/FilterBar';
import { StatsSkeleton, CardSkeleton } from '../components/common/Skeleton';
import { Alert } from '../components/common/Alert';
import {
  TrendingUp, MessageSquare, Layers, Globe, Download,
  ChevronLeft, ChevronRight, X, Filter, Eye,
} from 'lucide-react';
import type { AnalyzedEntry, FilterParams, TopicCluster } from '../types';
import { api } from '../services/api';

const PAGE_SIZE = 50;

export function DashboardPage() {
  const { jobs, currentResult, activeJobId, loading, error, loadJobs, selectJob, exportResults, setError } = useAnalysis();
  const [selectedTopic, setSelectedTopic] = useState<TopicCluster | null>(null);

  // Pagination & filtering state
  const [filters, setFilters] = useState<FilterParams>({});
  const [page, setPage] = useState(1);
  const [filteredEntries, setFilteredEntries] = useState<AnalyzedEntry[]>([]);
  const [filteredTotal, setFilteredTotal] = useState(0);
  const [tableLoading, setTableLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Anomaly expansion
  const [expandedAnomaly, setExpandedAnomaly] = useState<string | null>(null);

  // Entry detail modal
  const [selectedEntry, setSelectedEntry] = useState<AnalyzedEntry | null>(null);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    if (jobs.length > 0 && !activeJobId) {
      const completed = jobs.find((j) => j.status === 'completed');
      if (completed) {
        selectJob(completed.job_id);
      }
    }
  }, [jobs, activeJobId, selectJob]);

  const result = currentResult;

  // Fetch paginated/filtered entries from backend
  const fetchEntries = useCallback(async (jobId: string, f: FilterParams, p: number) => {
    setTableLoading(true);
    try {
      const data = await api.filterResults(jobId, { ...f, page: p, page_size: PAGE_SIZE });
      setFilteredEntries(data.entries);
      setFilteredTotal(data.total);
    } catch {
      // fallback to client-side slice
      if (result) {
        setFilteredEntries(result.entries.slice((p - 1) * PAGE_SIZE, p * PAGE_SIZE));
        setFilteredTotal(result.entries.length);
      }
    } finally {
      setTableLoading(false);
    }
  }, [result]);

  // Load entries whenever result, filters, or page changes
  useEffect(() => {
    if (result?.job_id) {
      fetchEntries(result.job_id, filters, page);
    }
  }, [result?.job_id, filters, page, fetchEntries]);

  const totalPages = Math.ceil(filteredTotal / PAGE_SIZE);
  const hasActiveFilters = Object.values(filters).some((v) =>
    v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0 : true)
  );

  const applyFilter = (newFilters: Partial<FilterParams>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setPage(1);
  };

  if (loading && !result) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Loading analysis results…</p>
        </div>
        <StatsSkeleton />
        <div className="grid grid-2 mt-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div>
        <div className="page-header">
          <h2>Dashboard</h2>
          <p>Welcome to Topic Analysis. Upload data to get started.</p>
        </div>
        <div className="card">
          <div className="card-body" style={{ textAlign: 'center', padding: 60 }}>
            <MessageSquare size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
            <h3 style={{ color: 'var(--text-secondary)' }}>No analysis results yet</h3>
            <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>
              Go to <strong>Upload Data</strong> to analyze customer feedback, support tickets, or reviews.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const summary = result.summary;
  const topics = result.topics || [];
  const allLanguages = [...new Set(result.entries.map((e) => e.language.language))];
  const allSources = [...new Set(result.entries.map((e) => e.source).filter(Boolean))] as string[];
  const allTopicIds = [...new Set(topics.map((t) => t.topic_id))];

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Dashboard</h2>
          <p>
            Job: {result.job_id} • {result.total_entries} entries analyzed
            {result.completed_at && ` • Completed ${new Date(result.completed_at).toLocaleString()}`}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            className="select"
            value={activeJobId || ''}
            onChange={(e) => {
              selectJob(e.target.value);
              clearFilters();
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
          <button
            className="btn btn-secondary"
            onClick={() => exportResults(result.job_id, 'csv')}
            aria-label="Export CSV"
          >
            <Download size={14} /> CSV
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => exportResults(result.job_id, 'json')}
            aria-label="Export JSON"
          >
            <Download size={14} /> JSON
          </button>
          <button
            className="btn btn-primary"
            onClick={() => exportResults(result.job_id, 'pdf')}
            aria-label="Export PDF"
          >
            <Download size={14} /> PDF
          </button>
        </div>
      </div>

      {error && <Alert type="danger" message={error} onDismiss={() => setError(null)} />}

      {/* Clickable Anomaly Alerts */}
      {result.anomalies.length > 0 && (
        <div className="mb-4">
          {result.anomalies.slice(0, 5).map((a) => (
            <div key={a.id} className="mb-4">
              <div
                className={`alert alert-${a.severity === 'high' ? 'danger' : 'warning'} clickable-alert`}
                onClick={() => setExpandedAnomaly(expandedAnomaly === a.id ? null : a.id)}
                style={{ cursor: 'pointer' }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setExpandedAnomaly(expandedAnomaly === a.id ? null : a.id)}
              >
                <span style={{ flex: 1 }}>🚨 {a.message}</span>
                <span style={{ fontSize: 11, opacity: 0.7 }}>
                  {expandedAnomaly === a.id ? '▲ Hide details' : '▼ Click for details'}
                </span>
              </div>
              {expandedAnomaly === a.id && (
                <div className="card" style={{ marginTop: -1, borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
                  <div className="card-body">
                    <div className="grid grid-3 mb-4">
                      <div>
                        <div className="stat-label">Type</div>
                        <span className="badge badge-warning">{a.type.replace('_', ' ')}</span>
                      </div>
                      <div>
                        <div className="stat-label">Detected</div>
                        <span style={{ fontSize: 13 }}>{new Date(a.detected_at).toLocaleString()}</span>
                      </div>
                      <div>
                        <div className="stat-label">Severity</div>
                        <span className={`badge badge-${a.severity === 'high' ? 'negative' : 'warning'}`}>{a.severity}</span>
                      </div>
                    </div>
                    {a.details && Object.keys(a.details).length > 0 && (
                      <div>
                        <div className="stat-label" style={{ marginBottom: 8 }}>Details</div>
                        <div style={{ background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', padding: 12, fontSize: 12 }}>
                          {Object.entries(a.details).map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                              <span style={{ fontWeight: 600, color: 'var(--text-muted)', minWidth: 120 }}>{k}:</span>
                              <span style={{ color: 'var(--text-secondary)' }}>{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {a.type === 'sentiment_drop' && (
                      <button
                        className="btn btn-sm btn-secondary mt-4"
                        onClick={(e) => {
                          e.stopPropagation();
                          applyFilter({ sentiment_max: 0.3 });
                          setExpandedAnomaly(null);
                        }}
                      >
                        <Eye size={12} /> Show low-sentiment entries
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-4 mb-4">
        <div className="card stat-card">
          <div className="flex items-center gap-2">
            <MessageSquare size={16} style={{ color: 'var(--accent)' }} />
            <span className="stat-label">Total Entries</span>
          </div>
          <div className="stat-value">{summary?.total_entries || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} style={{ color: 'var(--success)' }} />
            <span className="stat-label">Avg Sentiment</span>
          </div>
          <div className="stat-value">{summary?.avg_sentiment?.toFixed(3) || '—'}</div>
          <span className={`badge badge-${summary?.dominant_sentiment || 'neutral'}`}>
            {summary?.dominant_sentiment || 'N/A'}
          </span>
        </div>
        <div className="card stat-card">
          <div className="flex items-center gap-2">
            <Layers size={16} style={{ color: 'var(--info)' }} />
            <span className="stat-label">Topics Found</span>
          </div>
          <div className="stat-value">{summary?.num_topics || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="flex items-center gap-2">
            <Globe size={16} style={{ color: 'var(--warning)' }} />
            <span className="stat-label">Languages</span>
          </div>
          <div className="stat-value">{summary?.languages_detected?.length || 0}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {summary?.languages_detected?.join(', ') || ''}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header">
            <h3>Sentiment Trend</h3>
          </div>
          <div className="card-body">
            <SentimentTrendChart data={result.sentiment_trends} />
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3>Topic Distribution</h3>
          </div>
          <div className="card-body">
            <TopicBarChart topics={topics} />
          </div>
        </div>
      </div>

      {/* Topic Graph */}
      {result.topic_graph && (
        <div className="card mb-4">
          <div className="card-header">
            <h3>Topic Clusters</h3>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Scroll to zoom • Click nodes for details
            </span>
          </div>
          <div className="card-body">
            <ForceGraph
              graph={result.topic_graph}
              height={400}
              onNodeClick={(topic) => setSelectedTopic(topic)}
            />
          </div>
        </div>
      )}

      {/* Selected Topic Detail */}
      {selectedTopic && (
        <div className="card mb-4">
          <div className="card-header">
            <h3>Topic: {selectedTopic.label}</h3>
            <div className="flex gap-2">
              <button
                className="btn btn-sm btn-primary"
                onClick={() => {
                  applyFilter({ topics: [selectedTopic.topic_id] });
                  setSelectedTopic(null);
                }}
              >
                <Filter size={12} /> Filter entries
              </button>
              <button className="btn-icon" onClick={() => setSelectedTopic(null)} aria-label="Close">×</button>
            </div>
          </div>
          <div className="card-body">
            <div className="grid grid-3">
              <div>
                <div className="stat-label">Size</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{selectedTopic.size} entries</div>
              </div>
              <div>
                <div className="stat-label">Avg Sentiment</div>
                <div style={{ fontSize: 20, fontWeight: 700 }}>{selectedTopic.avg_sentiment.toFixed(3)}</div>
              </div>
              <div>
                <div className="stat-label">Keywords</div>
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  {selectedTopic.keywords.slice(0, 8).map((kw) => (
                    <span key={kw} className="badge badge-info">{kw}</span>
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-4">
              <div className="stat-label">Sentiment Distribution</div>
              <SentimentDistribution
                positive={selectedTopic.sentiment_distribution.positive || 0}
                negative={selectedTopic.sentiment_distribution.negative || 0}
                neutral={selectedTopic.sentiment_distribution.neutral || 0}
              />
            </div>
            {selectedTopic.representative_docs.length > 0 && (
              <div className="mt-4">
                <div className="stat-label">Representative Documents</div>
                {selectedTopic.representative_docs.map((doc, i) => (
                  <div
                    key={i}
                    style={{
                      padding: 8,
                      background: 'var(--bg-secondary)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 12,
                      marginTop: 4,
                      color: 'var(--text-secondary)',
                    }}
                  >
                    "{doc}"
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Entry Detail Modal */}
      {selectedEntry && (
        <div className="modal-overlay" onClick={() => setSelectedEntry(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="card-header">
              <h3>Entry Detail</h3>
              <button className="btn-icon" onClick={() => setSelectedEntry(null)} aria-label="Close"><X size={14} /></button>
            </div>
            <div className="card-body">
              <div className="mb-4">
                <div className="stat-label">Full Text</div>
                <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)', marginTop: 4 }}>
                  {selectedEntry.text}
                </p>
              </div>
              <div className="grid grid-3 mb-4">
                <div>
                  <div className="stat-label">Sentiment</div>
                  <div className="flex gap-2 items-center" style={{ marginTop: 4 }}>
                    <span className={`badge badge-${selectedEntry.sentiment.label}`}>{selectedEntry.sentiment.label}</span>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>{selectedEntry.sentiment.score.toFixed(3)}</span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    Confidence: {(selectedEntry.sentiment.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="stat-label">Language</div>
                  <div style={{ marginTop: 4 }}>
                    <span className="badge badge-info">{selectedEntry.language.language}</span>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {(selectedEntry.language.confidence * 100).toFixed(1)}% ({selectedEntry.language.method})
                    </div>
                  </div>
                </div>
                <div>
                  <div className="stat-label">Topic</div>
                  <div style={{ fontSize: 14, fontWeight: 500, marginTop: 4 }}>{selectedEntry.topic_label || 'Uncategorized'}</div>
                </div>
              </div>
              <div className="grid grid-2">
                {selectedEntry.source && (
                  <div>
                    <div className="stat-label">Source</div>
                    <div style={{ fontSize: 14, marginTop: 4 }}>{selectedEntry.source}</div>
                  </div>
                )}
                {selectedEntry.timestamp && (
                  <div>
                    <div className="stat-label">Timestamp</div>
                    <div style={{ fontSize: 14, marginTop: 4 }}>{new Date(selectedEntry.timestamp).toLocaleString()}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Entries Table with Filters & Pagination */}
      <div className="card">
        <div className="card-header">
          <div className="flex items-center gap-2">
            <h3>Entries</h3>
            {hasActiveFilters && (
              <span className="badge badge-info" style={{ fontSize: 10 }}>Filtered</span>
            )}
          </div>
          <div className="flex gap-2 items-center">
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {filteredTotal === result.entries.length
                ? `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, filteredTotal)} of ${filteredTotal}`
                : `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, filteredTotal)} of ${filteredTotal} (filtered from ${result.entries.length})`
              }
            </span>
            <button
              className={`btn btn-sm ${showFilters ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter size={12} /> {showFilters ? 'Hide Filters' : 'Filters'}
            </button>
            {hasActiveFilters && (
              <button className="btn btn-sm btn-secondary" onClick={clearFilters}>
                <X size={12} /> Clear
              </button>
            )}
          </div>
        </div>

        {showFilters && (
          <FilterBar
            topics={allTopicIds}
            languages={allLanguages}
            sources={allSources}
            onFilter={(f) => {
              setFilters(f);
              setPage(1);
            }}
            onReset={clearFilters}
          />
        )}

        <div className="table-wrapper" style={{ opacity: tableLoading ? 0.6 : 1, transition: 'opacity 0.2s' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Text</th>
                <th>Sentiment</th>
                <th>Score</th>
                <th>Language</th>
                <th>Topic</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((entry) => (
                <tr key={entry.id} className="clickable-row" onClick={() => setSelectedEntry(entry)}>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {entry.text}
                  </td>
                  <td>
                    <span
                      className={`badge badge-${entry.sentiment.label} clickable-badge`}
                      onClick={(e) => {
                        e.stopPropagation();
                        applyFilter({
                          sentiment_min: entry.sentiment.label === 'positive' ? 0.6 : entry.sentiment.label === 'negative' ? 0 : 0.35,
                          sentiment_max: entry.sentiment.label === 'positive' ? 1 : entry.sentiment.label === 'negative' ? 0.35 : 0.6,
                        });
                      }}
                      title={`Filter by ${entry.sentiment.label}`}
                    >
                      {entry.sentiment.label}
                    </span>
                  </td>
                  <td>{entry.sentiment.score.toFixed(3)}</td>
                  <td>
                    <span
                      className="badge badge-info clickable-badge"
                      onClick={(e) => {
                        e.stopPropagation();
                        applyFilter({ languages: [entry.language.language] });
                      }}
                      title={`Filter by ${entry.language.language}`}
                    >
                      {entry.language.language}
                    </span>
                  </td>
                  <td>
                    <span
                      className="clickable-text"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (entry.topic_id !== -1) {
                          applyFilter({ topics: [entry.topic_id] });
                        }
                      }}
                      title={entry.topic_id !== -1 ? `Filter by this topic` : 'Uncategorized'}
                      style={{
                        maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block',
                        cursor: entry.topic_id !== -1 ? 'pointer' : 'default',
                      }}
                    >
                      {entry.topic_label || 'Uncategorized'}
                    </span>
                  </td>
                  <td>
                    {entry.source ? (
                      <span
                        className="clickable-text"
                        onClick={(e) => {
                          e.stopPropagation();
                          applyFilter({ sources: [entry.source!] });
                        }}
                        title={`Filter by ${entry.source}`}
                      >
                        {entry.source}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredEntries.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                    {tableLoading ? 'Loading…' : 'No entries match current filters'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="pagination">
            <button
              className="btn btn-sm btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage(1)}
              title="First page"
            >
              «
            </button>
            <button
              className="btn btn-sm btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              <ChevronLeft size={14} /> Previous
            </button>
            <div className="pagination-pages">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (page <= 3) {
                  pageNum = i + 1;
                } else if (page >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = page - 2 + i;
                }
                return (
                  <button
                    key={pageNum}
                    className={`btn btn-sm ${pageNum === page ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              className="btn btn-sm btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next <ChevronRight size={14} />
            </button>
            <button
              className="btn btn-sm btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage(totalPages)}
              title="Last page"
            >
              »
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
