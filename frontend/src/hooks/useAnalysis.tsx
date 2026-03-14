import { useState, useCallback, useContext, createContext, type ReactNode } from 'react';
import type { AnalysisResult, FilterParams, JobStatus } from '../types';
import { api } from '../services/api';

interface AnalysisState {
  jobs: JobStatus[];
  currentResult: AnalysisResult | null;
  activeJobId: string | null;
  loading: boolean;
  error: string | null;
  uploadFile: (file: File, source?: string) => Promise<JobStatus>;
  loadJobs: () => Promise<void>;
  loadResult: (jobId: string) => Promise<AnalysisResult | undefined>;
  selectJob: (jobId: string) => void;
  pollJobStatus: (jobId: string, onUpdate?: (status: JobStatus) => void) => Promise<void>;
  exportResults: (jobId: string, format: 'csv' | 'json' | 'pdf', filters?: FilterParams) => Promise<void>;
  setError: (error: string | null) => void;
}

const AnalysisContext = createContext<AnalysisState | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [currentResult, setCurrentResult] = useState<AnalysisResult | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(async (file: File, source?: string) => {
    setLoading(true);
    setError(null);
    try {
      const useChunked = file.size > 10 * 1024 * 1024;
      const status = useChunked ? await api.uploadChunked(file) : await api.uploadFile(file, source);
      setJobs((prev) => [status, ...prev]);
      return status;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadJobs = useCallback(async () => {
    try {
      const data = await api.getJobs();
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    }
  }, []);

  const loadResult = useCallback(async (jobId: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getJobResult(jobId);
      setCurrentResult(result);
      setActiveJobId(jobId);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const selectJob = useCallback((jobId: string) => {
    setActiveJobId(jobId);
    loadResult(jobId);
  }, [loadResult]);

  const pollJobStatus = useCallback(
    async (jobId: string, onUpdate?: (status: JobStatus) => void) => {
      const poll = async () => {
        try {
          const status = await api.getJobStatus(jobId);
          onUpdate?.(status);
          if (status.status === 'completed') {
            await loadResult(jobId);
            return;
          }
          if (status.status === 'failed') {
            setError('Analysis failed');
            return;
          }
          setTimeout(poll, 2000);
        } catch {
          setTimeout(poll, 5000);
        }
      };
      poll();
    },
    [loadResult],
  );

  const exportResults = useCallback(async (jobId: string, format: 'csv' | 'json' | 'pdf', filters?: FilterParams) => {
    try {
      const blob = await api.exportResults(jobId, format, filters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_${jobId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  }, []);

  return (
    <AnalysisContext.Provider
      value={{
        jobs,
        currentResult,
        activeJobId,
        loading,
        error,
        uploadFile,
        loadJobs,
        loadResult,
        selectJob,
        pollJobStatus,
        exportResults,
        setError,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis(): AnalysisState {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
