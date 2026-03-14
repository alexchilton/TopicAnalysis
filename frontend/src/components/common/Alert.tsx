import { AlertCircle, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface AlertProps {
  type: 'success' | 'danger' | 'warning' | 'info';
  message: string;
  onDismiss?: () => void;
}

const icons = {
  success: CheckCircle,
  danger: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

export function Alert({ type, message, onDismiss }: AlertProps) {
  const Icon = icons[type];

  return (
    <div className={`alert alert-${type}`} role="alert">
      <Icon size={16} />
      <span style={{ flex: 1 }}>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="btn-icon"
          style={{ border: 'none', padding: 4 }}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
}
