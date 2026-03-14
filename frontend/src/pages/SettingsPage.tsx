import { useState, useEffect } from 'react';
import { Save, Key, Bell, Sliders, RefreshCw, CheckCircle } from 'lucide-react';
import { Alert } from '../components/common/Alert';

interface AppSettings {
  apiKey: string;
  pageSize: number;
  anomalyThreshold: number;
  enableNotifications: boolean;
  slackWebhookUrl: string;
  autoRefreshInterval: number;
}

const STORAGE_KEY = 'topicanalysis-settings';

function loadSettings(): AppSettings {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return { ...defaultSettings, ...JSON.parse(stored) };
  } catch {
    // ignore
  }
  return defaultSettings;
}

const defaultSettings: AppSettings = {
  apiKey: localStorage.getItem('api-key') || 'dev-key-1',
  pageSize: 50,
  anomalyThreshold: 1.5,
  enableNotifications: false,
  slackWebhookUrl: '',
  autoRefreshInterval: 0,
};

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings>(loadSettings);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testingApi, setTestingApi] = useState(false);
  const [apiStatus, setApiStatus] = useState<'unknown' | 'ok' | 'error'>('unknown');

  useEffect(() => {
    testApiConnection(settings.apiKey);
  }, []);

  const testApiConnection = async (key: string) => {
    setTestingApi(true);
    try {
      const resp = await fetch('/api/v1/jobs', {
        headers: { 'X-API-Key': key },
      });
      setApiStatus(resp.ok ? 'ok' : 'error');
    } catch {
      setApiStatus('error');
    } finally {
      setTestingApi(false);
    }
  };

  const handleSave = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      localStorage.setItem('api-key', settings.apiKey);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      setError('Failed to save settings');
    }
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.setItem('api-key', defaultSettings.apiKey);
    setSaved(false);
  };

  const update = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h2>Settings</h2>
          <p>Configure API access, display preferences, and notification settings</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={handleReset}>
            <RefreshCw size={14} /> Reset
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            <Save size={14} /> Save Settings
          </button>
        </div>
      </div>

      {error && <Alert type="danger" message={error} onDismiss={() => setError(null)} />}
      {saved && (
        <div className="alert alert-success mb-4">
          <CheckCircle size={16} />
          <span>Settings saved. Some changes may require a page reload.</span>
        </div>
      )}

      {/* API Configuration */}
      <div className="card mb-4">
        <div className="card-header">
          <div className="flex items-center gap-2">
            <Key size={16} />
            <h3>API Configuration</h3>
          </div>
          <span className={`badge ${apiStatus === 'ok' ? 'badge-positive' : apiStatus === 'error' ? 'badge-negative' : 'badge-neutral'}`}>
            {apiStatus === 'ok' ? 'Connected' : apiStatus === 'error' ? 'Error' : 'Unknown'}
          </span>
        </div>
        <div className="card-body">
          <div className="filter-group mb-4">
            <label className="label" htmlFor="api-key">API Key</label>
            <div className="flex gap-2">
              <input
                id="api-key"
                type="password"
                className="input"
                value={settings.apiKey}
                onChange={(e) => update('apiKey', e.target.value)}
                placeholder="Enter API key"
              />
              <button
                className="btn btn-secondary"
                onClick={() => testApiConnection(settings.apiKey)}
                disabled={testingApi}
              >
                {testingApi ? 'Testing…' : 'Test'}
              </button>
            </div>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Default: dev-key-1 for development
            </span>
          </div>
        </div>
      </div>

      {/* Display Preferences */}
      <div className="card mb-4">
        <div className="card-header">
          <div className="flex items-center gap-2">
            <Sliders size={16} />
            <h3>Display Preferences</h3>
          </div>
        </div>
        <div className="card-body">
          <div className="filter-group mb-4">
            <label className="label" htmlFor="page-size">Entries Per Page</label>
            <select
              id="page-size"
              className="select"
              value={settings.pageSize}
              onChange={(e) => update('pageSize', Number(e.target.value))}
            >
              <option value={25}>25</option>
              <option value={50}>50 (Default)</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
            </select>
          </div>
          <div className="filter-group mb-4">
            <label className="label" htmlFor="auto-refresh">Auto-Refresh Interval (seconds)</label>
            <select
              id="auto-refresh"
              className="select"
              value={settings.autoRefreshInterval}
              onChange={(e) => update('autoRefreshInterval', Number(e.target.value))}
            >
              <option value={0}>Disabled</option>
              <option value={10}>10 seconds</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
            </select>
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Automatically refresh dashboard data at this interval
            </span>
          </div>
        </div>
      </div>

      {/* Anomaly Detection */}
      <div className="card mb-4">
        <div className="card-header">
          <div className="flex items-center gap-2">
            <Bell size={16} />
            <h3>Anomaly Detection & Notifications</h3>
          </div>
        </div>
        <div className="card-body">
          <div className="filter-group mb-4">
            <label className="label" htmlFor="anomaly-threshold">Sentiment Z-Score Threshold</label>
            <input
              id="anomaly-threshold"
              type="number"
              className="input"
              value={settings.anomalyThreshold}
              onChange={(e) => update('anomalyThreshold', Number(e.target.value))}
              step={0.1}
              min={0.5}
              max={5}
            />
            <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              Alert when sentiment deviates by this many standard deviations (lower = more sensitive)
            </span>
          </div>
          <div className="filter-group mb-4">
            <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                checked={settings.enableNotifications}
                onChange={(e) => update('enableNotifications', e.target.checked)}
              />
              Enable Slack Notifications
            </label>
          </div>
          {settings.enableNotifications && (
            <div className="filter-group">
              <label className="label" htmlFor="slack-webhook">Slack Webhook URL</label>
              <input
                id="slack-webhook"
                type="url"
                className="input"
                value={settings.slackWebhookUrl}
                onChange={(e) => update('slackWebhookUrl', e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
              />
            </div>
          )}
        </div>
      </div>

      {/* System Info */}
      <div className="card">
        <div className="card-header">
          <h3>System Information</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-2">
            <div>
              <div className="stat-label">Frontend Version</div>
              <div style={{ fontWeight: 600 }}>1.0.0</div>
            </div>
            <div>
              <div className="stat-label">API Endpoint</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>/api/v1</div>
            </div>
            <div>
              <div className="stat-label">Theme</div>
              <div style={{ fontWeight: 600 }}>
                {document.documentElement.getAttribute('data-theme') || 'light'}
              </div>
            </div>
            <div>
              <div className="stat-label">Storage Used</div>
              <div style={{ fontWeight: 600 }}>
                {((JSON.stringify(localStorage).length / 1024)).toFixed(1)} KB
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
