import { AuditLog } from '../api';

interface Props {
  logs: AuditLog[];
}

export function AuditLogs({ logs }: Props) {
  return (
    <div className="card">
      <h2>Logs de Auditoria</h2>
      {logs.length === 0 ? (
        <div className="empty">Nenhum log registrado</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Ação</th>
              <th>Ator</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {logs.slice(0, 10).map((l) => (
              <tr key={l.id}>
                <td>{l.event_type}</td>
                <td>{l.action}</td>
                <td>{l.actor}</td>
                <td>{new Date(l.created_at).toLocaleString('pt-BR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
