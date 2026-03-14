import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  ShieldCheck,
  GitCompareArrows,
  Sun,
  Moon,
  Settings,
} from 'lucide-react';
import type { Theme } from '../../types';

interface SidebarProps {
  theme: Theme;
  onToggleTheme: () => void;
}

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload', icon: Upload, label: 'Upload Data' },
  { to: '/quality', icon: ShieldCheck, label: 'Data Quality' },
  { to: '/compare', icon: GitCompareArrows, label: 'Compare' },
];

export function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  return (
    <aside className="sidebar" role="navigation" aria-label="Main navigation">
      <div className="sidebar-header">
        <h1>📊 TopicAnalysis</h1>
        <span>Sentiment & Topic Dashboard</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            tabIndex={0}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item" onClick={onToggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
        <NavLink
          to="/settings"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          tabIndex={0}
        >
          <Settings size={18} />
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
