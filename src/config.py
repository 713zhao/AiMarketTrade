"""
Configuration management for deerflow-openbb system.
Loads environment variables with validation and defaults.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # API Keys
    fmp_api_key: Optional[str] = Field(None, alias="FMP_API_KEY")
    polygon_api_key: Optional[str] = Field(None, alias="POLYGON_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(None, alias="ALPHA_VANTAGE_API_KEY")
    eodhd_api_key: Optional[str] = Field(None, alias="EODHD_API_KEY")
    benzinga_api_key: Optional[str] = Field(None, alias="BENZINGA_API_KEY")

    # LLM Keys
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")

    # System Configuration
    default_llm_model: str = Field("gpt-4", alias="DEFAULT_LLM_MODEL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Trading Configuration
    default_tickers: List[str] = Field(["AAPL", "MSFT", "GOOGL"], alias="DEFAULT_TICKERS")
    time_horizon: str = Field("MEDIUM", alias="TIME_HORIZON")
    risk_tolerance: str = Field("MODERATE", alias="RISK_TOLERANCE")
    max_position_size: float = Field(5.0, alias="MAX_POSITION_SIZE")

    # Data provider priority (comma-separated)
    data_provider_priority: List[str] = Field(
        ["fmp", "polygon", "yahoo", "alpha_vantage"],
        alias="DATA_PROVIDER_PRIORITY"
    )

    # Analysis Configuration
    min_data_points: int = Field(252, description="Minimum historical data points (1 year)")
    technical_indicators: List[str] = Field(
        ["SMA_20", "SMA_50", "SMA_200", "RSI_14", "MACD", "BB_UPPER", "BB_LOWER", "ATR_14"],
        description="Technical indicators to calculate"
    )

    # Graph Configuration
    max_parallel_analysts: int = Field(3, description="Maximum concurrent analyst nodes")
    graph_checkpoint_dir: str = Field("./checkpoints", description="Directory for graph checkpoints")

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "__",
        "case_sensitive": False,
        "extra": "allow"
    }

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("time_horizon")
    @classmethod
    def validate_time_horizon(cls, v: str) -> str:
        """Validate time horizon."""
        valid_horizons = {"SHORT", "MEDIUM", "LONG"}
        v_upper = v.upper()
        if v_upper not in valid_horizons:
            raise ValueError(f"time_horizon must be one of {valid_horizons}")
        return v_upper

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk_tolerance(cls, v: str) -> str:
        """Validate risk tolerance."""
        valid_risks = {"CONSERVATIVE", "MODERATE", "AGGRESSIVE"}
        v_upper = v.upper()
        if v_upper not in valid_risks:
            raise ValueError(f"risk_tolerance must be one of {valid_risks}")
        return v_upper

    def get_available_data_providers(self) -> List[str]:
        """Get list of data providers with valid API keys."""
        providers = []
        if self.fmp_api_key:
            providers.append("fmp")
        if self.polygon_api_key:
            providers.append("polygon")
        if self.alpha_vantage_api_key:
            providers.append("alpha_vantage")
        if self.eodhd_api_key:
            providers.append("eodhd")
        # Yahoo Finance is always available (free)
        providers.append("yahoo")
        return providers

    def get_primary_data_provider(self) -> str:
        """Get the highest priority data provider with a valid API key."""
        available = self.get_available_data_providers()
        for provider in self.data_provider_priority:
            if provider in available:
                return provider
        # Fallback to yahoo finance
        return "yahoo"

    def requires_api_key(self, provider: str) -> bool:
        """Check if a data provider requires an API key."""
        free_providers = {"yahoo"}
        return provider not in free_providers


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings
