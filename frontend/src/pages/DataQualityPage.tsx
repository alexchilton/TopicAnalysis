import { useEffect } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import { DataQualityPanel } from '../components/quality/DataQualityPanel';
import { CardSkeleton } from '../components/common/Skeleton';

export function DataQualityPage() {
  const { jobs, currentResult, activeJobId, loading, loadJobs, selectJob } = useAnalysis();

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    if (jobs.length > 0 && !activeJobId) {
      const completed = jobs.find((j) => j.status === 'completed');
      if (completed) selectJob(completed.job_id);
    }
  }, [jobs, activeJobId, selectJob]);

  if (loading && !currentResult) {
    return (
      <div>
        <div className="page-header">
          <h2>Data Quality</h2>
        </div>
        <CardSkeleton />
      </div>
    );
  }

  if (!currentResult?.data_quality) {
    return (
      <div>
        <div className="page-header">
          <h2>Data Quality</h2>
          <p>No data quality report available. Upload and analyze data first.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Data Quality</h2>
          <p>Review data quality issues — click cards to drill down into affected entries</p>
        </div>
        {jobs.filter((j) => j.status === 'completed').length > 1 && (
          <select
            className="select"
            value={activeJobId || ''}
            onChange={(e) => selectJob(e.target.value)}
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
      <DataQualityPanel report={currentResult.data_quality} entries={currentResult.entries} />
    </div>
  );
}
