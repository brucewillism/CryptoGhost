import { ConsensusData } from '../api';

interface Props {
  consensus: ConsensusData | null;
}

export function AIConfidenceMeter({ consensus }: Props) {
  const confidence = consensus?.confidence ?? 0;
  const pct = Math.round(confidence * 100);
  const decision = consensus?.final_decision ?? 'HOLD';

  const color = decision === 'BUY' ? 'var(--accent)' : decision === 'SELL' ? 'var(--danger)' : 'var(--warning)';

  return (
    <div className="card terminal-panel">
      <h2>AI Confidence Meter</h2>
      <div className="confidence-meter">
        <div className="confidence-ring" style={{ '--pct': pct, '--color': color } as React.CSSProperties}>
          <span className="confidence-value">{pct}%</span>
          <span className="confidence-decision">{decision}</span>
        </div>
        {consensus && (
          <div className="confidence-meta">
            <span>Concordância: {consensus.agreement}/{consensus.agreement + consensus.disagreement} agentes</span>
            {consensus.conflicts && consensus.conflicts.length > 0 && (
              <span className="conflict-warning">⚠ {consensus.conflicts.length} conflito(s)</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
