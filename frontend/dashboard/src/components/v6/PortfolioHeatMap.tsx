interface Props {
  risk: Record<string, unknown> | null;
}

export function PortfolioHeatMap({ risk }: Props) {
  if (!risk) return <p className="v6-empty">—</p>;
  const exposure = Number(risk.total_exposure || 0);
  const maxExp = Number(risk.max_exposure || 1);
  const heat = Math.min(100, Math.round((exposure / maxExp) * 100));
  const color = heat > 80 ? '#ef4444' : heat > 50 ? '#f59e0b' : '#22c55e';
  return (
    <div className="v6-heat-map">
      <div className="v6-heat-bar" style={{ background: `linear-gradient(90deg, ${color} ${heat}%, #1e293b ${heat}%)` }} />
      <p>Heat: {heat}% · ${exposure.toFixed(0)} / ${maxExp.toFixed(0)}</p>
    </div>
  );
}

export function RiskExposurePanel({ risk }: Props) {
  if (!risk) return <p className="v6-empty">—</p>;
  return (
    <>
      <p>Exposição: ${Number(risk.total_exposure || 0).toFixed(0)}</p>
      <p>Max: ${Number(risk.max_exposure || 0).toFixed(0)}</p>
      <p>P&L dia: ${Number(risk.daily_pnl || 0).toFixed(2)}</p>
      <p className="v6-meta">Posições: {String(risk.open_positions ?? '—')}</p>
    </>
  );
}
