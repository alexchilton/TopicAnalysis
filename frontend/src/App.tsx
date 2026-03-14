import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { ComparePage } from './pages/ComparePage';
import { SettingsPage } from './pages/SettingsPage';
import { AnalysisProvider } from './hooks/useAnalysis';
import { useTheme } from './hooks/useTheme';
import './styles/globals.css';

export default function App() {
  const { theme, toggleTheme } = useTheme();

  return (
    <BrowserRouter>
      <AnalysisProvider>
        <div className="app-layout">
          <Sidebar theme={theme} onToggleTheme={toggleTheme} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/quality" element={<DataQualityPage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </AnalysisProvider>
    </BrowserRouter>
  );
}
