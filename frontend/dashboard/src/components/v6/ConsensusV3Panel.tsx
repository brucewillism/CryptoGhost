interface Props {
  data: Record<string, unknown> | null;
}

export function ConsensusV3Panel({ data }: Props) {
  if (!data?.final_score) return <p className="v6-empty">Sem sinal v6</p>;
  return (
    <>
      <p className="v6-score">{String(data.final_score)}</p>
      <p>{String(data.classification)} · {String(data.final_decision)}</p>
      <p className="v6-meta">
        Concordância: {String(data.agreement)} · Exec: {data.can_execute ? 'Sim' : 'Não'}
      </p>
      {Array.isArray(data.rejection_reasons) && (data.rejection_reasons as string[]).length > 0 && (
        <p className="v6-meta">{(data.rejection_reasons as string[]).join(', ')}</p>
      )}
    </>
  );
}
