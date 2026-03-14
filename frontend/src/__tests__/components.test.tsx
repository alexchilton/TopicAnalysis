import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { server } from '../__mocks__/handlers';
import { Sidebar } from '../components/layout/Sidebar';
import { Alert } from '../components/common/Alert';
import { Skeleton } from '../components/common/Skeleton';
import { DataQualityPanel } from '../components/quality/DataQualityPanel';
import type { DataQualityReport } from '../types';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Sidebar', () => {
  it('renders navigation items', () => {
    render(
      <BrowserRouter>
        <Sidebar theme="dark" onToggleTheme={() => {}} />
      </BrowserRouter>,
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Upload Data')).toBeInTheDocument();
    expect(screen.getByText('Data Quality')).toBeInTheDocument();
    expect(screen.getByText('Compare')).toBeInTheDocument();
  });

  it('renders theme toggle button', () => {
    render(
      <BrowserRouter>
        <Sidebar theme="dark" onToggleTheme={() => {}} />
      </BrowserRouter>,
    );

    expect(screen.getByText('Light Mode')).toBeInTheDocument();
  });

  it('shows dark mode text when theme is light', () => {
    render(
      <BrowserRouter>
        <Sidebar theme="light" onToggleTheme={() => {}} />
      </BrowserRouter>,
    );

    expect(screen.getByText('Dark Mode')).toBeInTheDocument();
  });
});

describe('Alert', () => {
  it('renders danger alert', () => {
    render(<Alert type="danger" message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders success alert', () => {
    render(<Alert type="success" message="Operation completed" />);
    expect(screen.getByText('Operation completed')).toBeInTheDocument();
  });

  it('calls onDismiss when close button clicked', async () => {
    const onDismiss = vi.fn();
    render(<Alert type="warning" message="Warning" onDismiss={onDismiss} />);

    const dismissBtn = screen.getByLabelText('Dismiss');
    dismissBtn.click();
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});

describe('Skeleton', () => {
  it('renders loading skeleton', () => {
    render(<Skeleton variant="text" count={3} />);
    const skeletons = screen.getAllByRole('status');
    expect(skeletons).toHaveLength(3);
  });
});

describe('DataQualityPanel', () => {
  const mockReport: DataQualityReport = {
    total_entries: 100,
    low_confidence_count: 5,
    low_confidence_entries: ['1', '2', '3', '4', '5'],
    mixed_language_count: 3,
    mixed_language_entries: ['6', '7', '8'],
    duplicate_count: 2,
    duplicate_entries: ['9', '10'],
    avg_confidence: 0.85,
    language_distribution: { en: 80, es: 12, fr: 8 },
  };

  it('renders quality stats', () => {
    render(<DataQualityPanel report={mockReport} />);

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows health score', () => {
    render(<DataQualityPanel report={mockReport} />);
    expect(screen.getByText('Data Health Score')).toBeInTheDocument();
  });

  it('displays language distribution', () => {
    render(<DataQualityPanel report={mockReport} />);
    expect(screen.getByText('en: 80')).toBeInTheDocument();
    expect(screen.getByText('es: 12')).toBeInTheDocument();
  });

  it('shows warning when issues exist', () => {
    render(<DataQualityPanel report={mockReport} />);
    expect(screen.getByText(/data quality issue/i)).toBeInTheDocument();
  });
});
