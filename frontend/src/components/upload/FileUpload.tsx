import { useState, useCallback, useRef } from 'react';
import { Upload, FileText, X } from 'lucide-react';

interface FileUploadProps {
  onUpload: (file: File, source?: string) => Promise<void>;
  loading?: boolean;
}

const ACCEPTED_TYPES = [
  '.csv',
  '.json',
  '.xlsx',
  '.xls',
  '.zip',
  'text/csv',
  'application/json',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/zip',
];

export function FileUpload({ onUpload, loading }: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [source, setSource] = useState('');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!['.csv', '.json', '.xlsx', '.xls', '.zip'].includes(ext)) {
      setError(`Unsupported format: ${ext}. Use CSV, JSON, Excel, or ZIP.`);
      return false;
    }
    if (file.size > 500 * 1024 * 1024) {
      setError('File too large. Maximum 500MB.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleSubmit = async () => {
    if (!selectedFile) return;
    try {
      await onUpload(selectedFile, source || undefined);
      setSelectedFile(null);
      setSource('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div>
      <div
        className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload file"
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <Upload size={32} style={{ color: 'var(--accent)' }} />
        <h3>Drop files here or click to browse</h3>
        <p>Supports CSV, JSON, Excel (.xlsx/.xls), and ZIP files up to 500MB</p>
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
          Files &gt;10MB will be uploaded in chunks automatically
        </p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES.join(',')}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
          aria-hidden="true"
        />
      </div>

      {error && (
        <div className="alert alert-danger mt-4">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="btn-icon" style={{ border: 'none', marginLeft: 'auto' }}>×</button>
        </div>
      )}

      {selectedFile && (
        <div className="card mt-4">
          <div className="card-body flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText size={20} style={{ color: 'var(--accent)' }} />
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedFile.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{formatSize(selectedFile.size)}</div>
              </div>
            </div>
            <button className="btn-icon" onClick={() => setSelectedFile(null)} aria-label="Remove file">
              <X size={16} />
            </button>
          </div>
          <div className="card-body" style={{ paddingTop: 0 }}>
            <div className="filter-group" style={{ maxWidth: 300 }}>
              <label className="label" htmlFor="source-input">Data Source (optional)</label>
              <input
                id="source-input"
                className="input"
                placeholder="e.g., app_store, survey, support"
                value={source}
                onChange={(e) => setSource(e.target.value)}
              />
            </div>
            <button
              className="btn btn-primary mt-4"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? 'Uploading…' : 'Start Analysis'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
