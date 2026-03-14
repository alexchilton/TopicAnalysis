import type { AnalysisResult, ComparisonResult, FilterParams, JobStatus } from '../types';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public correlationId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getHeaders(): Record<string, string> {
  const apiKey = localStorage.getItem('api_key') || 'dev-key-1';
  return {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json',
  };
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail || 'Request failed', body.correlation_id);
  }
  return response.json();
}

export const api = {
  async uploadFile(file: File, source?: string): Promise<JobStatus> {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (source) params.set('source', source);

    const apiKey = localStorage.getItem('api_key') || 'dev-key-1';
    const response = await fetch(`${API_BASE}/upload?${params}`, {
      method: 'POST',
      headers: { 'X-API-Key': apiKey },
      body: formData,
    });

    return handleResponse<JobStatus>(response);
  },

  async uploadChunked(
    file: File,
    onProgress?: (progress: number) => void,
  ): Promise<JobStatus> {
    const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    let uploadId: string | undefined;
    let lastStatus: JobStatus | undefined;

    for (let i = 0; i < totalChunks; i++) {
      const start = i * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const chunk = file.slice(start, end);

      const formData = new FormData();
      formData.append('file', chunk, file.name);

      const params = new URLSearchParams({
        chunk_index: String(i),
        total_chunks: String(totalChunks),
      });
      if (uploadId) params.set('upload_id', uploadId);

      const apiKey = localStorage.getItem('api_key') || 'dev-key-1';
      const response = await fetch(`${API_BASE}/upload/chunked?${params}`, {
        method: 'POST',
        headers: { 'X-API-Key': apiKey },
        body: formData,
      });

      lastStatus = await handleResponse<JobStatus>(response);
      uploadId = lastStatus.job_id;
      onProgress?.((i + 1) / totalChunks);
    }

    return lastStatus!;
  },

  async getJobs(): Promise<JobStatus[]> {
    const response = await fetch(`${API_BASE}/jobs`, { headers: getHeaders() });
    return handleResponse<JobStatus[]>(response);
  },

  async getJobResult(jobId: string): Promise<AnalysisResult> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`, { headers: getHeaders() });
    return handleResponse<AnalysisResult>(response);
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/status`, { headers: getHeaders() });
    return handleResponse<JobStatus>(response);
  },

  async filterResults(jobId: string, filters: FilterParams) {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/filter`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(filters),
    });
    return handleResponse<{ total: number; page: number; entries: AnalysisResult['entries'] }>(response);
  },

  async compareSegments(jobId: string, segmentA: FilterParams, segmentB: FilterParams): Promise<ComparisonResult> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/compare`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ segment_a: segmentA, segment_b: segmentB }),
    });
    return handleResponse<ComparisonResult>(response);
  },

  async exportResults(jobId: string, format: 'csv' | 'json' | 'pdf', filters?: FilterParams): Promise<Blob> {
    const response = await fetch(`${API_BASE}/jobs/${jobId}/export?fmt=${format}`, {
      method: 'POST',
      headers: getHeaders(),
      body: filters ? JSON.stringify(filters) : '{}',
    });

    if (!response.ok) {
      throw new ApiError(response.status, 'Export failed');
    }
    return response.blob();
  },

  subscribeToEvents(onMessage: (data: Record<string, unknown>) => void): EventSource {
    const apiKey = localStorage.getItem('api_key') || 'dev-key-1';
    const es = new EventSource(`${API_BASE}/events/analysis?api_key=${apiKey}`);

    es.addEventListener('analysis_update', (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch {
        // ignore parse errors
      }
    });

    return es;
  },
};
