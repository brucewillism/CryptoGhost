interface AgentRecord {
  agent: string;
  accuracy: number;
  weight: number;
  regime?: string;
}

interface Props {
  records: AgentRecord[];
  weights?: Record<string, number>;
}

export function AgentAccuracyChart({ records, weights }: Props) {
  if (!records.length) return <p className="v6-empty">Sem dados de agentes</p>;
  return (
    <div className="v6-agent-chart">
      {records.slice(0, 8).map((a) => {
        const pct = Math.round(a.accuracy * 100);
        const w = weights?.[a.agent] ?? a.weight ?? 0;
        return (
          <div key={a.agent} className="v6-bar-row">
            <span className="v6-bar-label">{a.agent}</span>
            <div className="v6-bar-track">
              <div className="v6-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="v6-bar-value">{pct}% · w={Number(w).toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}
