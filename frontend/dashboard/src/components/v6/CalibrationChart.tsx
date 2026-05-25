interface Props {
  learning: Record<string, unknown> | null;
}

export function CalibrationChart({ learning }: Props) {
  if (!learning) return <p className="v6-empty">—</p>;
  const hit = ((learning.hit_rate as number) ?? 0) * 100;
  const threshold = ((learning.adaptive_threshold as number) ?? 0.65) * 100;
  return (
    <div className="v6-calibration">
      <div className="v6-bar-row">
        <span className="v6-bar-label">Hit rate</span>
        <div className="v6-bar-track"><div className="v6-bar-fill green" style={{ width: `${hit}%` }} /></div>
        <span className="v6-bar-value">{hit.toFixed(1)}%</span>
      </div>
      <div className="v6-bar-row">
        <span className="v6-bar-label">Threshold</span>
        <div className="v6-bar-track"><div className="v6-bar-fill blue" style={{ width: `${threshold}%` }} /></div>
        <span className="v6-bar-value">{threshold.toFixed(0)}%</span>
      </div>
    </div>
  );
}

export function DriftMonitor({ learning }: Props) {
  if (!learning) return <p className="v6-empty">—</p>;
  const drift = Boolean(learning.drift_detected);
  return (
    <div className={`v6-drift ${drift ? 'alert' : 'ok'}`}>
      <p>{drift ? '⚠ Drift detectado — recalibração recomendada' : '✓ Modelos estáveis'}</p>
      {Boolean(learning.recalibration_triggered) && <p className="v6-meta">Recalibração acionada</p>}
    </div>
  );
}
