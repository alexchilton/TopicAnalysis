export interface SentimentResult {
  label: 'positive' | 'negative' | 'neutral';
  score: number;
  confidence: number;
}

export interface LanguageResult {
  language: string;
  confidence: number;
  method: string;
}

export interface AnalyzedEntry {
  id: string;
  text: string;
  source?: string;
  timestamp?: string;
  sentiment: SentimentResult;
  language: LanguageResult;
  topic_id: number;
  topic_label: string;
  metadata?: Record<string, unknown>;
}

export interface TopicCluster {
  topic_id: number;
  label: string;
  keywords: string[];
  size: number;
  avg_sentiment: number;
  sentiment_distribution: Record<string, number>;
  languages: Record<string, number>;
  representative_docs: string[];
}

export interface TopicLink {
  source: number;
  target: number;
  weight: number;
}

export interface TopicGraph {
  nodes: TopicCluster[];
  links: TopicLink[];
}

export interface SentimentTrend {
  period: string;
  avg_sentiment: number;
  count: number;
  positive: number;
  negative: number;
  neutral: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface DataQualityReport {
  total_entries: number;
  low_confidence_count: number;
  low_confidence_entries: string[];
  mixed_language_count: number;
  mixed_language_entries: string[];
  duplicate_count: number;
  duplicate_entries: string[];
  avg_confidence: number;
  language_distribution: Record<string, number>;
}

export interface AnomalyAlert {
  id: string;
  type: 'sentiment_drop' | 'topic_spike';
  severity: string;
  message: string;
  detected_at: string;
  details: Record<string, unknown>;
}

export interface TopicInfo {
  topic_id: number;
  label: string;
  keywords: string[];
  size: number;
}

export interface AnalysisSummary {
  total_entries: number;
  avg_sentiment: number;
  dominant_sentiment: string;
  num_topics: number;
  top_topics: TopicInfo[];
  languages_detected: string[];
  date_range?: { start: string; end: string };
}

export interface AnalysisResult {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  total_entries: number;
  entries: AnalyzedEntry[];
  topics: TopicCluster[];
  sentiment_trends: SentimentTrend[];
  topic_graph?: TopicGraph;
  data_quality?: DataQualityReport;
  anomalies: AnomalyAlert[];
  summary?: AnalysisSummary;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
}

export interface FilterParams {
  date_from?: string;
  date_to?: string;
  sentiment_min?: number;
  sentiment_max?: number;
  topics?: number[];
  languages?: string[];
  sources?: string[];
  search_text?: string;
  page?: number;
  page_size?: number;
}

export interface ComparisonResult {
  segment_a: AnalysisSummary;
  segment_b: AnalysisSummary;
  sentiment_delta: number;
  topic_changes: Record<string, unknown>[];
  new_topics: TopicInfo[];
  disappeared_topics: TopicInfo[];
}

export type Theme = 'light' | 'dark';
