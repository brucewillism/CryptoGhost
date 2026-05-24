import { Order } from '../api';

interface Props {
  orders: Order[];
}

export function OrdersTable({ orders }: Props) {
  return (
    <div className="card">
      <h2>Operações Recentes</h2>
      {orders.length === 0 ? (
        <div className="empty">Nenhuma ordem registrada</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Símbolo</th>
              <th>Lado</th>
              <th>Status</th>
              <th>Modo</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {orders.slice(0, 10).map((o) => (
              <tr key={o.id}>
                <td>{o.symbol}</td>
                <td className={o.side === 'buy' ? 'side-buy' : 'side-sell'}>{o.side.toUpperCase()}</td>
                <td>{o.status}</td>
                <td>{o.trading_mode}</td>
                <td>{new Date(o.created_at).toLocaleString('pt-BR')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
