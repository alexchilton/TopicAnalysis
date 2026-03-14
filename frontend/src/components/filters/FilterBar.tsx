import { useState } from 'react';
import type { FilterParams } from '../../types';

interface FilterBarProps {
  topics: number[];
  languages: string[];
  sources: string[];
  onFilter: (filters: FilterParams) => void;
  onReset: () => void;
}

export function FilterBar({ topics, languages, sources, onFilter, onReset }: FilterBarProps) {
  const [filters, setFilters] = useState<FilterParams>({});

  const handleChange = (key: keyof FilterParams, value: unknown) => {
    const updated = { ...filters, [key]: value || undefined };
    setFilters(updated);
  };

  const handleApply = () => {
    onFilter(filters);
  };

  const handleReset = () => {
    setFilters({});
    onReset();
  };

  return (
    <div className="filters-bar" role="search" aria-label="Filter results">
      <div className="filter-group">
        <label className="label" htmlFor="filter-date-from">Date From</label>
        <input
          id="filter-date-from"
          type="date"
          className="input"
          value={filters.date_from?.split('T')[0] || ''}
          onChange={(e) => handleChange('date_from', e.target.value ? e.target.value + 'T00:00:00' : undefined)}
        />
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-date-to">Date To</label>
        <input
          id="filter-date-to"
          type="date"
          className="input"
          value={filters.date_to?.split('T')[0] || ''}
          onChange={(e) => handleChange('date_to', e.target.value ? e.target.value + 'T23:59:59' : undefined)}
        />
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-sentiment">Sentiment Range</label>
        <div className="flex gap-2">
          <input
            type="number"
            className="input"
            placeholder="Min"
            min={0}
            max={1}
            step={0.1}
            style={{ width: 70 }}
            value={filters.sentiment_min ?? ''}
            onChange={(e) => handleChange('sentiment_min', e.target.value ? Number(e.target.value) : undefined)}
          />
          <input
            type="number"
            className="input"
            placeholder="Max"
            min={0}
            max={1}
            step={0.1}
            style={{ width: 70 }}
            value={filters.sentiment_max ?? ''}
            onChange={(e) => handleChange('sentiment_max', e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-language">Language</label>
        <select
          id="filter-language"
          className="select"
          value={filters.languages?.[0] || ''}
          onChange={(e) => handleChange('languages', e.target.value ? [e.target.value] : undefined)}
        >
          <option value="">All</option>
          {languages.map((lang) => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-source">Source</label>
        <select
          id="filter-source"
          className="select"
          value={filters.sources?.[0] || ''}
          onChange={(e) => handleChange('sources', e.target.value ? [e.target.value] : undefined)}
        >
          <option value="">All</option>
          {sources.map((src) => (
            <option key={src} value={src}>{src}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-topic">Topic</label>
        <select
          id="filter-topic"
          className="select"
          value={filters.topics?.[0]?.toString() || ''}
          onChange={(e) => handleChange('topics', e.target.value ? [Number(e.target.value)] : undefined)}
        >
          <option value="">All</option>
          {topics.filter((t) => t !== -1).map((t) => (
            <option key={t} value={t}>Topic {t}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label className="label" htmlFor="filter-search">Search</label>
        <input
          id="filter-search"
          className="input"
          placeholder="Search text…"
          value={filters.search_text || ''}
          onChange={(e) => handleChange('search_text', e.target.value || undefined)}
          style={{ width: 160 }}
        />
      </div>

      <div className="flex gap-2" style={{ alignSelf: 'flex-end' }}>
        <button className="btn btn-primary btn-sm" onClick={handleApply}>Apply</button>
        <button className="btn btn-secondary btn-sm" onClick={handleReset}>Reset</button>
      </div>
    </div>
  );
}
