import { ConsensusData } from '../api';

interface Props {
  consensus: ConsensusData | null;
}

export function ConsensusPanel({ consensus }: Props) {
  if (!consensus || !consensus.agent_votes) {
    return <div className="card terminal-panel"><h2>AI Consensus</h2><div className="empty">Sem dados de consenso</div></div>;
  }

  return (
    <div className="card terminal-panel">
      <h2>Multi-Agent Consensus</h2>
      <div className="consensus-header">
        <span className={`decision-badge ${consensus.final_decision.toLowerCase()}`}>{consensus.final_decision}</span>
        <span>{(consensus.confidence * 100).toFixed(0)}%</span>
      </div>
      <div className="agent-votes">
        {consensus.agent_votes.map((v) => (
          <div key={v.agent} className="agent-vote">
            <span className="agent-name">{v.agent}</span>
            <span className={`agent-decision ${v.decision.toLowerCase()}`}>{v.decision}</span>
            <div className="agent-conf-bar">
              <div className="bar-fill" style={{ width: `${v.confidence * 100}%` }} />
            </div>
            <span>{(v.confidence * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
