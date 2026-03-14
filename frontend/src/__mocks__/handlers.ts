import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import type { AnalysisResult, JobStatus } from '../types';

const mockJobStatus: JobStatus = {
  job_id: 'test-job-1',
  status: 'completed',
  progress: 1.0,
  message: 'Analysis complete',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:05:00Z',
};

const mockAnalysisResult: AnalysisResult = {
  job_id: 'test-job-1',
  status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:05:00Z',
  total_entries: 3,
  entries: [
    {
      id: '1',
      text: 'Great product!',
      source: 'survey',
      timestamp: '2024-01-01T00:00:00Z',
      sentiment: { label: 'positive', score: 0.9, confidence: 0.95 },
      language: { language: 'en', confidence: 0.99, method: 'langdetect' },
      topic_id: 0,
      topic_label: 'Product Quality',
    },
    {
      id: '2',
      text: 'Terrible service',
      source: 'email',
      timestamp: '2024-01-02T00:00:00Z',
      sentiment: { label: 'negative', score: 0.2, confidence: 0.88 },
      language: { language: 'en', confidence: 0.98, method: 'langdetect' },
      topic_id: 1,
      topic_label: 'Customer Service',
    },
    {
      id: '3',
      text: 'It works fine',
      source: 'chat',
      timestamp: '2024-01-03T00:00:00Z',
      sentiment: { label: 'neutral', score: 0.5, confidence: 0.7 },
      language: { language: 'en', confidence: 0.95, method: 'langdetect' },
      topic_id: 0,
      topic_label: 'Product Quality',
    },
  ],
  topics: [
    {
      topic_id: 0,
      label: 'Product Quality',
      keywords: ['product', 'quality', 'great'],
      size: 2,
      avg_sentiment: 0.7,
      sentiment_distribution: { positive: 1, neutral: 1, negative: 0 },
      languages: { en: 2 },
      representative_docs: ['Great product!', 'It works fine'],
    },
    {
      topic_id: 1,
      label: 'Customer Service',
      keywords: ['service', 'support', 'help'],
      size: 1,
      avg_sentiment: 0.2,
      sentiment_distribution: { positive: 0, neutral: 0, negative: 1 },
      languages: { en: 1 },
      representative_docs: ['Terrible service'],
    },
  ],
  sentiment_trends: [
    {
      period: '2024-01-01',
      avg_sentiment: 0.9,
      count: 1,
      positive: 1,
      negative: 0,
      neutral: 0,
      confidence_lower: 0.8,
      confidence_upper: 1.0,
    },
    {
      period: '2024-01-02',
      avg_sentiment: 0.2,
      count: 1,
      positive: 0,
      negative: 1,
      neutral: 0,
      confidence_lower: 0.1,
      confidence_upper: 0.3,
    },
  ],
  topic_graph: {
    nodes: [
      {
        topic_id: 0,
        label: 'Product Quality',
        keywords: ['product'],
        size: 2,
        avg_sentiment: 0.7,
        sentiment_distribution: { positive: 1, neutral: 1 },
        languages: { en: 2 },
        representative_docs: [],
      },
    ],
    links: [],
  },
  data_quality: {
    total_entries: 3,
    low_confidence_count: 0,
    low_confidence_entries: [],
    mixed_language_count: 0,
    mixed_language_entries: [],
    duplicate_count: 0,
    duplicate_entries: [],
    avg_confidence: 0.843,
    language_distribution: { en: 3 },
  },
  anomalies: [],
  summary: {
    total_entries: 3,
    avg_sentiment: 0.533,
    dominant_sentiment: 'positive',
    num_topics: 2,
    top_topics: [
      { topic_id: 0, label: 'Product Quality', keywords: ['product'], size: 2 },
      { topic_id: 1, label: 'Customer Service', keywords: ['service'], size: 1 },
    ],
    languages_detected: ['en'],
    date_range: { start: '2024-01-01', end: '2024-01-03' },
  },
};

export const handlers = [
  http.get('/api/v1/jobs', () => {
    return HttpResponse.json([mockJobStatus]);
  }),

  http.get('/api/v1/jobs/:jobId', () => {
    return HttpResponse.json(mockAnalysisResult);
  }),

  http.get('/api/v1/jobs/:jobId/status', () => {
    return HttpResponse.json(mockJobStatus);
  }),

  http.post('/api/v1/upload', () => {
    return HttpResponse.json(mockJobStatus);
  }),

  http.post('/api/v1/jobs/:jobId/filter', () => {
    return HttpResponse.json({
      total: 3,
      page: 1,
      entries: mockAnalysisResult.entries,
    });
  }),

  http.post('/api/v1/jobs/:jobId/compare', () => {
    return HttpResponse.json({
      segment_a: mockAnalysisResult.summary,
      segment_b: mockAnalysisResult.summary,
      sentiment_delta: 0.1,
      topic_changes: [],
      new_topics: [],
      disappeared_topics: [],
    });
  }),

  http.get('/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '1.0.0',
      models_loaded: true,
      redis_connected: true,
      uptime_seconds: 100,
    });
  }),
];

export const server = setupServer(...handlers);
export { mockAnalysisResult, mockJobStatus };
