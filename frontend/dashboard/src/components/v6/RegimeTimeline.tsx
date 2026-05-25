interface Props {
  regime: Record<string, unknown> | null;
}

export function RegimeTimeline({ regime }: Props) {
  if (!regime?.regime) return <p className="v6-empty">—</p>;
  const policy = regime.policy as Record<string, unknown> | undefined;
  return (
    <>
      <p className="v6-score">{String(regime.regime)}</p>
      <p>Conf: {((regime.confidence as number) * 100).toFixed(0)}%</p>
      {policy && (
        <p className="v6-meta">
          Exp×{String(policy.exposure_multiplier)} · min score {String(policy.min_final_score)}
        </p>
      )}
    </>
  );
}
