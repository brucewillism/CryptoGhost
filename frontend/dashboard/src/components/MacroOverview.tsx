import { MacroData } from '../api';

interface Props {
  macro: MacroData | null;
}

export function MacroOverview({ macro }: Props) {
  if (!macro) return <div className="card terminal-panel"><h2>Macro Overview</h2><div className="empty">Carregando...</div></div>;

  return (
    <div className="card terminal-panel">
      <h2>Macro Overview</h2>
      {macro.outlook && <div className="macro-outlook">Outlook: <strong>{macro.outlook}</strong></div>}
      <div className="macro-grid">
        {macro.indicators.map((ind) => (
          <div key={ind.name} className="macro-item">
            <span className="macro-name">{ind.name.replace(/_/g, ' ')}</span>
            <span className="macro-value">{ind.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
            {ind.change_pct !== undefined && ind.change_pct !== null && (
              <span className={`macro-change ${ind.change_pct >= 0 ? 'positive' : 'negative'}`}>
                {ind.change_pct >= 0 ? '+' : ''}{ind.change_pct.toFixed(2)}%
              </span>
            )}
            {ind.impact && <span className={`macro-impact ${ind.impact}`}>{ind.impact}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
