import { useAnalysis } from '../hooks/useAnalysis';
import { FileUpload } from '../components/upload/FileUpload';
import { Alert } from '../components/common/Alert';
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const statusIcons = {
  pending: Clock,
  processing: Loader,
  completed: CheckCircle,
  failed: XCircle,
};

const statusColors = {
  pending: 'var(--text-muted)',
  processing: 'var(--info)',
  completed: 'var(--success)',
  failed: 'var(--danger)',
};

export function UploadPage() {
  const { jobs, loading, error, uploadFile, pollJobStatus, setError } = useAnalysis();
  const navigate = useNavigate();

  const handleUpload = async (file: File, source?: string) => {
    const status = await uploadFile(file, source);
    pollJobStatus(status.job_id, (updated) => {
      if (updated.status === 'completed') {
        navigate('/');
      }
    });
  };

  return (
    <div>
      <div className="page-header">
        <h2>Upload Data</h2>
        <p>Upload customer feedback, support tickets, or reviews for analysis</p>
      </div>

      {error && <Alert type="danger" message={error} onDismiss={() => setError(null)} />}

      <FileUpload onUpload={handleUpload} loading={loading} />

      {jobs.length > 0 && (
        <div className="card mt-4">
          <div className="card-header">
            <h3>Analysis Jobs</h3>
          </div>
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Created</th>
                  <th>Message</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => {
                  const Icon = statusIcons[job.status];
                  return (
                    <tr key={job.job_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>{job.job_id}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Icon size={14} style={{ color: statusColors[job.status] }} />
                          {job.status}
                        </div>
                      </td>
                      <td>
                        <div className="progress-bar" style={{ width: 80 }}>
                          <div className="progress-fill" style={{ width: `${job.progress * 100}%` }} />
                        </div>
                      </td>
                      <td style={{ fontSize: 12 }}>{new Date(job.created_at).toLocaleString()}</td>
                      <td style={{ fontSize: 12 }}>{job.message}</td>
                      <td>
                        {job.status === 'completed' && (
                          <button className="btn btn-sm btn-primary" onClick={() => navigate('/')}>
                            View
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
