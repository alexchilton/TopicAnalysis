import { useState } from 'react';
import type { AnalyzedEntry, DataQualityReport } from '../../types';
import { AlertTriangle, Copy, Globe, TrendingDown, ChevronDown, ChevronUp } from 'lucide-react';

interface DataQualityPanelProps {
  report: DataQualityReport;
  entries?: AnalyzedEntry[];
}

type DrillDownType = 'low_confidence' | 'mixed_language' | 'duplicates' | null;

export function DataQualityPanel({ report, entries = [] }: DataQualityPanelProps) {
  const [drillDown, setDrillDown] = useState<DrillDownType>(null);
  const issueCount = report.low_confidence_count + report.mixed_language_count + report.duplicate_count;
  const healthScore = Math.max(0, 100 - (issueCount / Math.max(1, report.total_entries)) * 100);

  const toggleDrillDown = (type: DrillDownType) => {
    setDrillDown(drillDown === type ? null : type);
  };

  const getDrillDownEntries = (): AnalyzedEntry[] => {
    if (!drillDown || entries.length === 0) return [];
    const idSet = new Set(
      drillDown === 'low_confidence' ? report.low_confidence_entries
        : drillDown === 'mixed_language' ? report.mixed_language_entries
        : report.duplicate_entries
    );
    return entries.filter((e) => idSet.has(e.id));
  };

  const drillDownEntries = getDrillDownEntries();

  return (
    <div>
      <div className="grid grid-3 mb-4">
        <div
          className={`card stat-card clickable-card ${drillDown === 'low_confidence' ? 'active-drill' : ''}`}
          onClick={() => toggleDrillDown('low_confidence')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && toggleDrillDown('low_confidence')}
        >
          <div className="flex items-center gap-2">
            <TrendingDown size={16} style={{ color: 'var(--warning)' }} />
            <span className="stat-label">Low Confidence</span>
          </div>
          <div className="stat-value">{report.low_confidence_count}</div>
          <div className="flex justify-between items-center">
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              predictions below 50% confidence
            </span>
            {report.low_confidence_count > 0 && (
              drillDown === 'low_confidence'
                ? <ChevronUp size={14} style={{ color: 'var(--accent)' }} />
                : <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
            )}
          </div>
        </div>

        <div
          className={`card stat-card clickable-card ${drillDown === 'mixed_language' ? 'active-drill' : ''}`}
          onClick={() => toggleDrillDown('mixed_language')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && toggleDrillDown('mixed_language')}
        >
          <div className="flex items-center gap-2">
            <Globe size={16} style={{ color: 'var(--info)' }} />
            <span className="stat-label">Mixed Language</span>
          </div>
          <div className="stat-value">{report.mixed_language_count}</div>
          <div className="flex justify-between items-center">
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              entries differ from majority language
            </span>
            {report.mixed_language_count > 0 && (
              drillDown === 'mixed_language'
                ? <ChevronUp size={14} style={{ color: 'var(--accent)' }} />
                : <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
            )}
          </div>
        </div>

        <div
          className={`card stat-card clickable-card ${drillDown === 'duplicates' ? 'active-drill' : ''}`}
          onClick={() => toggleDrillDown('duplicates')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && toggleDrillDown('duplicates')}
        >
          <div className="flex items-center gap-2">
            <Copy size={16} style={{ color: 'var(--danger)' }} />
            <span className="stat-label">Duplicates</span>
          </div>
          <div className="stat-value">{report.duplicate_count}</div>
          <div className="flex justify-between items-center">
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              exact or near-duplicate entries
            </span>
            {report.duplicate_count > 0 && (
              drillDown === 'duplicates'
                ? <ChevronUp size={14} style={{ color: 'var(--accent)' }} />
                : <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
            )}
          </div>
        </div>
      </div>

      {/* Drill-down entries table */}
      {drillDown && (
        <div className="card mb-4">
          <div className="card-header">
            <h3>
              {drillDown === 'low_confidence' ? 'Low Confidence Entries' :
               drillDown === 'mixed_language' ? 'Mixed Language Entries' :
               'Duplicate Entries'}
            </h3>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {drillDownEntries.length > 0
                ? `${drillDownEntries.length} entries`
                : `${drillDown === 'low_confidence' ? report.low_confidence_count : drillDown === 'mixed_language' ? report.mixed_language_count : report.duplicate_count} entry IDs found`}
            </span>
          </div>
          <div className="table-wrapper">
            {drillDownEntries.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Text</th>
                    <th>Sentiment</th>
                    <th>Confidence</th>
                    <th>Language</th>
                    {drillDown === 'low_confidence' && <th>Score</th>}
                  </tr>
                </thead>
                <tbody>
                  {drillDownEntries.slice(0, 50).map((entry) => (
                    <tr key={entry.id}>
                      <td style={{ maxWidth: 350, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {entry.text}
                      </td>
                      <td>
                        <span className={`badge badge-${entry.sentiment.label}`}>{entry.sentiment.label}</span>
                      </td>
                      <td>
                        <span style={{
                          color: entry.sentiment.confidence < 0.5 ? 'var(--danger)' : 'var(--text-secondary)',
                          fontWeight: entry.sentiment.confidence < 0.5 ? 600 : 400,
                        }}>
                          {(entry.sentiment.confidence * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-info">{entry.language.language}</span>
                      </td>
                      {drillDown === 'low_confidence' && (
                        <td>{entry.sentiment.score.toFixed(3)}</td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="card-body" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <p>Entry details not available. IDs:</p>
                <div className="flex gap-2" style={{ flexWrap: 'wrap', justifyContent: 'center', marginTop: 8 }}>
                  {(drillDown === 'low_confidence' ? report.low_confidence_entries :
                    drillDown === 'mixed_language' ? report.mixed_language_entries :
                    report.duplicate_entries).slice(0, 20).map((id) => (
                    <span key={id} className="badge badge-neutral" style={{ fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-header">
          <h3>Data Health Score</h3>
          <span className={`badge ${healthScore > 80 ? 'badge-positive' : healthScore > 50 ? 'badge-warning' : 'badge-negative'}`}>
            {healthScore.toFixed(0)}%
          </span>
        </div>
        <div className="card-body">
          <div className="progress-bar" style={{ height: 12, borderRadius: 6 }}>
            <div
              className="progress-fill"
              style={{
                width: `${healthScore}%`,
                background: healthScore > 80 ? 'var(--success)' : healthScore > 50 ? 'var(--warning)' : 'var(--danger)',
              }}
            />
          </div>

          <div className="mt-4">
            <div className="stat-label" style={{ marginBottom: 8 }}>Language Distribution</div>
            <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
              {Object.entries(report.language_distribution).map(([lang, count]) => (
                <span key={lang} className="badge badge-info">
                  {lang}: {count}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <div className="stat-label">Average Confidence</div>
            <div style={{ fontSize: 20, fontWeight: 700 }}>
              {(report.avg_confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {issueCount > 0 && (
        <div className="alert alert-warning mt-4">
          <AlertTriangle size={16} />
          <span>
            {issueCount} data quality issue{issueCount !== 1 ? 's' : ''} detected.
            Click the cards above to review affected entries.
          </span>
        </div>
      )}
    </div>
  );
}
