"""CryptoGhost - Configurações centralizadas via variáveis de ambiente."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptoGhostSettings(BaseSettings):
    """Configurações do CryptoGhost carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CRYPTOGHOST_",
        case_sensitive=False,
        extra="ignore",
    )

    # Aplicação
    env: Literal["development", "staging", "production", "test"] = "development"
    app_name: str = "CryptoGhost"
    secret_key: str = Field(min_length=32)
    debug: bool = False
    paper_trading: bool = True
    live_trading_enabled: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # JWT
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Database
    database_url: str
    database_url_sync: str

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Exchanges
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    alpaca_paper: bool = True

    # Risk Management
    max_daily_loss_pct: float = 2.0
    max_exposure_pct: float = 10.0
    default_stop_loss_pct: float = 1.5
    default_take_profit_pct: float = 3.0
    trailing_stop_pct: float = 0.5
    circuit_breaker_enabled: bool = True

    # Observability
    sentry_dsn: str = ""
    prometheus_enabled: bool = True

    # Notifications
    notification_webhook: str = ""
    notification_email: str = ""

    # Users
    admin_username: str = "bruce"
    admin_password: str = "change-me"

    # AI Providers
    ai_provider_default: str = "ollama"
    ollama_enabled: bool = True
    ollama_url: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_model_primary: str = ""
    ollama_model_secondary: str = ""
    ollama_model_reasoning: str = ""
    ollama_model_embedding: str = ""
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout: float = 0.0
    ollama_retry_max: int = 3
    ollama_retry_backoff: float = 1.5
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ai_request_timeout: float = 60.0
    finbert_enabled: bool = True
    embedding_dimensions: int = 384

    # Intelligence
    intelligence_symbols: str = "BTC/USDT,ETH/USDT,SOL/USDT"
    intelligence_analysis_interval: int = 120

    # Quant v3
    ollama_models: str = "llama3,deepseek-r1,mistral,qwen2.5,phi3"
    rl_training_episodes: int = 50
    gpu_inference_enabled: bool = True
    feature_store_ttl: int = 300
    event_bus_enabled: bool = True

    # Investment v4
    investment_universe: str = "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,ADA/USDT"
    max_single_allocation_pct: float = 35.0
    min_cash_allocation_pct: float = 20.0
    premium_ai_for_explanations: bool = True

    # Self-improving v5
    data_lake_path: str = "data/lake"
    self_improvement_enabled: bool = True
    drift_retrain_threshold: float = 0.2
    survival_emergency_threshold: float = 25.0

    # Premium data APIs (optional)
    fred_api_key: str = ""
    glassnode_api_key: str = ""
    coinglass_api_key: str = ""
    alphavantage_api_key: str = ""
    santiment_api_key: str = ""
    finnhub_api_key: str = ""
    polygon_api_key: str = ""

    @property
    def intelligence_symbols_list(self) -> list[str]:
        return [s.strip() for s in self.intelligence_symbols.split(",") if s.strip()]

    @property
    def ollama_models_list(self) -> list[str]:
        return [m.strip() for m in self.ollama_models.split(",") if m.strip()]

    @property
    def investment_universe_list(self) -> list[str]:
        return [s.strip() for s in self.investment_universe.split(",") if s.strip()]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: str) -> str:
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_ollama_base_url(self) -> str:
        return (self.ollama_url or self.ollama_base_url).rstrip("/")

    @property
    def effective_ollama_model(self) -> str:
        return self.ollama_model_primary or self.ollama_model or "llama3.2:latest"

    @property
    def effective_ollama_model_secondary(self) -> str:
        return self.ollama_model_secondary or "deepseek-r1"

    @property
    def effective_ollama_embed_model(self) -> str:
        return self.ollama_model_embedding or self.ollama_embed_model or "nomic-embed-text"

    @property
    def effective_ollama_timeout(self) -> float:
        return self.ollama_timeout if self.ollama_timeout > 0 else self.ai_request_timeout

    @model_validator(mode="after")
    def resolve_ollama_aliases(self) -> "CryptoGhostSettings":
        if self.ollama_url:
            object.__setattr__(self, "ollama_base_url", self.ollama_url.rstrip("/"))
        if self.ollama_model_primary:
            object.__setattr__(self, "ollama_model", self.ollama_model_primary)
        if self.ollama_model_embedding:
            object.__setattr__(self, "ollama_embed_model", self.ollama_model_embedding)
        return self

    @model_validator(mode="after")
    def enforce_trading_safety(self) -> "CryptoGhostSettings":
        if self.env in ("development", "test") and self.live_trading_enabled:
            object.__setattr__(self, "live_trading_enabled", False)
        if self.paper_trading:
            object.__setattr__(self, "live_trading_enabled", False)
        return self

    @property
    def is_live_trading_allowed(self) -> bool:
        """Trading real só é permitido com confirmação explícita."""
        return self.live_trading_enabled and not self.paper_trading and self.env == "production"


@lru_cache
def get_settings() -> CryptoGhostSettings:
    """Retorna instância cacheada das configurações."""
    return CryptoGhostSettings()
