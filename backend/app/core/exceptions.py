"""CryptoGhost v6 — exceções."""


class V6Error(Exception):
    """Base exception for v6 layer."""


class DataProviderError(V6Error):
    """Falha ao obter dados de mercado."""


class SignalStaleError(V6Error):
    """Sinal expirado ou ausente."""


class RiskRejectedError(V6Error):
    """Ordem rejeitada pelo risk engine."""


class ConsensusRejectedError(V6Error):
    """Consenso abaixo do threshold."""
