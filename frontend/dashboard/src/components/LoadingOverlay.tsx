import { useEffect, useState } from 'react';

interface LoadingOverlayProps {
  message: string;
  submessage?: string;
  showElapsed?: boolean;
}

export function LoadingOverlay({ message, submessage, showElapsed = false }: LoadingOverlayProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!showElapsed) return;
    setElapsed(0);
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [showElapsed, message]);

  const mins = Math.floor(elapsed / 60);
  const secs = elapsed % 60;
  const elapsedLabel = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;

  return (
    <div className="loading-overlay" role="status" aria-live="polite">
      <div className="loading-card">
        <span className="loading-logo">👻</span>
        <div className="loading-spinner" />
        <h2 className="loading-title">{message}</h2>
        {submessage && <p className="loading-sub">{submessage}</p>}
        {showElapsed && <p className="loading-elapsed">{elapsedLabel} decorrido</p>}
      </div>
    </div>
  );
}
