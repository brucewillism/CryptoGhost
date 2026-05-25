import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

interface Props {
  onCycleComplete: () => void;
  onRunningChange?: (running: boolean) => void;
}

export function AutonomousInvestor({ onCycleComplete, onRunningChange }: Props) {
  const [status, setStatus] = useState('IA autônoma ativa — analisando e investindo em paper');
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [intervalMin, setIntervalMin] = useState(30);
  const started = useRef(false);

  useEffect(() => {
    api.getStats()
      .then((s) => setIntervalMin(s.auto_invest_interval_minutes ?? 30))
      .catch(() => api.getV6Config().then((c) => setIntervalMin(c.auto_invest_interval_minutes ?? 30)).catch(() => {}));
  }, []);

  const runCycle = async () => {
    if (running) return;
    setRunning(true);
    onRunningChange?.(true);
    setStatus('Ciclo autônomo em execução...');
    try {
      await api.startPaperTrial().catch(() => {});
      const result = await api.runAutonomousCycle();
      const sym = result.recommendation?.symbol || '—';
      const order = result.order;
      if (order?.executed) {
        setStatus(`✓ Investiu em ${sym} automaticamente (paper)`);
      } else if (order?.status === 'no_opportunity') {
        setStatus(`Analisado — aguardando oportunidade (último: ${sym})`);
      } else if (order?.status === 'rejected') {
        setStatus('Oportunidade detectada, mas risk manager bloqueou a ordem');
      } else {
        setStatus(`Analisado ${sym} — sem compra (sinal fraco)`);
      }
      setLastRun(new Date().toLocaleTimeString('pt-BR'));
      onCycleComplete();
    } catch {
      setStatus('Ciclo autônomo falhou — tentará de novo em breve');
    } finally {
      setRunning(false);
      onRunningChange?.(false);
    }
  };

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const t = setTimeout(runCycle, 45_000);
    const interval = setInterval(runCycle, intervalMin * 60 * 1000);
    return () => { clearTimeout(t); clearInterval(interval); };
  }, [intervalMin]);

  return (
    <section className="terminal-row">
      <div className="card terminal-panel autonomous-panel">
        <div className="autonomous-header">
          <h2>🤖 IA Autônoma — Paper Trading</h2>
          <span className="auto-badge">SEM APROVAÇÃO MANUAL</span>
        </div>
        <p className="autonomous-desc">
          A IA analisa o mercado, investe sozinha em modo paper e aprende com os resultados.
          Ciclo automático a cada {intervalMin} minutos.
        </p>
        <p className={`autonomous-status ${running ? 'running' : ''}`}>
          {running && <span className="autonomous-spinner" aria-hidden="true" />}
          {status}
        </p>
        {lastRun && <p className="autonomous-last">Último ciclo: {lastRun}</p>}
        <button className="analyze-btn" onClick={runCycle} disabled={running}>
          {running ? 'Executando...' : 'Forçar ciclo agora'}
        </button>
      </div>
    </section>
  );
}
