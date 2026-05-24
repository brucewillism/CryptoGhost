import { ExplanationData } from '../api';

interface Props {
  explanation: ExplanationData | null;
}

export function AIExplanationPanel({ explanation }: Props) {
  if (!explanation || !explanation.reasons) {
    return (
      <div className="card terminal-panel explanation-panel">
        <h2>AI Explanation (XAI)</h2>
        <div className="empty">Execute uma análise para ver explicações</div>
      </div>
    );
  }

  return (
    <div className="card terminal-panel explanation-panel">
      <h2>AI Explanation (XAI)</h2>
      <div className="explanation-decision">
        <span className={`decision-badge ${explanation.decision.toLowerCase()}`}>{explanation.decision}</span>
        <span className="explanation-conf">{(explanation.confidence * 100).toFixed(0)}% confiança</span>
      </div>
      <p className="explanation-text">{explanation.textual_explanation}</p>
      <ul className="explanation-reasons">
        {explanation.reasons.map((r, i) => (
          <li key={i}>{r}</li>
        ))}
      </ul>
      {explanation.feature_importance && (
        <div className="feature-importance">
          <h3>Feature Importance</h3>
          {Object.entries(explanation.feature_importance).slice(0, 5).map(([k, v]) => (
            <div key={k} className="feature-bar">
              <span>{k}</span>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${v * 100}%` }} /></div>
              <span>{(v * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
