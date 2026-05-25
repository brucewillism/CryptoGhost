import { useState } from 'react';
import { api } from '../api';

interface Props {
  onLogin: () => void;
  sessionMessage?: string;
}

export function LoginForm({ onLogin, sessionMessage }: Props) {
  const [username, setUsername] = useState('bruce');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    const ok = await api.login(username, password);
    setLoading(false);
    if (ok) {
      onLogin();
    } else {
      setError('Usuário ou senha inválidos');
    }
  };

  return (
    <div className="login-container">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>👻 CryptoGhost</h1>
        <p>Dashboard de Trading · Acesso Restrito</p>
        {sessionMessage && <div className="login-info">{sessionMessage}</div>}
        <input
          type="text"
          placeholder="Usuário"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Senha"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
        {error && <div className="login-error">{error}</div>}
      </form>
    </div>
  );
}
