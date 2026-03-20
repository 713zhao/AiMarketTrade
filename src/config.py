"""
Configuration management for deerflow-openbb system.
Loads environment variables with validation and defaults.
"""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ConfigDict
import os
import json


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
    default_tickers: List[str] = Field(
        default=["AAPL", "MSFT", "GOOGL"], 
        alias="DEFAULT_TICKERS",
        description="Default tickers to analyze (comma-separated or JSON list)"
    )
    time_horizon: str = Field("MEDIUM", alias="TIME_HORIZON")
    risk_tolerance: str = Field("MODERATE", alias="RISK_TOLERANCE")
    max_position_size: float = Field(5.0, alias="MAX_POSITION_SIZE")

    # Data provider priority (comma-separated or JSON list)
    data_provider_priority: List[str] = Field(
        default=["fmp", "polygon", "yahoo", "alpha_vantage"],
        alias="DATA_PROVIDER_PRIORITY",
        description="Data provider priority (comma-separated or JSON list)"
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

    # Virtual Trading Configuration
    trading_enabled: bool = Field(
        False,
        alias="TRADING_ENABLED",
        description="Enable virtual trading execution"
    )
    trading_initial_capital: float = Field(
        100000.0,
        alias="TRADING_INITIAL_CAPITAL",
        description="Starting capital for virtual portfolio",
        gt=0.0
    )
    trading_position_size_pct: float = Field(
        0.10,
        alias="TRADING_POSITION_SIZE_PCT",
        description="Position size as % of portfolio per trade (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    trading_confidence_threshold: float = Field(
        0.70,
        alias="TRADING_CONFIDENCE_THRESHOLD",
        description="Minimum signal confidence to execute trade",
        ge=0.0,
        le=1.0
    )
    trading_slippage_pct: float = Field(
        0.001,
        alias="TRADING_SLIPPAGE_PCT",
        description="Slippage percentage per trade",
        ge=0.0,
        le=0.1
    )
    trading_commission_pct: float = Field(
        0.0001,
        alias="TRADING_COMMISSION_PCT",
        description="Commission percentage per trade",
        ge=0.0,
        le=0.01
    )

    # Hybrid Scanning Configuration (Two-Stage Analysis)
    hybrid_scan_enabled: bool = Field(
        True,
        alias="HYBRID_SCAN_ENABLED",
        description="Enable two-stage hybrid scanning (quick filter + deep analysis)"
    )
    quick_scan_min_score: float = Field(
        2.0,
        alias="QUICK_SCAN_MIN_SCORE",
        description="Minimum score to pass quick scan filter (out of 5)",
        ge=0.0,
        le=5.0
    )
    quick_scan_max_candidates: int = Field(
        20,
        alias="QUICK_SCAN_MAX_CANDIDATES",
        description="Maximum candidates to analyze in deep phase",
        ge=1
    )
    deep_analysis_min_score: float = Field(
        3.5,
        alias="DEEP_ANALYSIS_MIN_SCORE",
        description="Minimum score to recommend from deep analysis (out of 10)",
        ge=0.0,
        le=10.0
    )
    deep_analysis_max_score_diff: float = Field(
        2.0,
        alias="DEEP_ANALYSIS_MAX_SCORE_DIFF",
        description="Maximum allowed difference between quick and deep scores",
        ge=0.0
    )
    deep_analysis_require_agreement: bool = Field(
        True,
        alias="DEEP_ANALYSIS_REQUIRE_AGREEMENT",
        description="If true, quick and deep signals must match (BUY/SELL)",
        alias_priority=True
    )
    quick_scan_timeout_secs: float = Field(
        5.0,
        alias="QUICK_SCAN_TIMEOUT_SECS",
        description="Timeout for quick scan in seconds"
    )
    deep_analysis_timeout_secs: float = Field(
        30.0,
        alias="DEEP_ANALYSIS_TIMEOUT_SECS",
        description="Timeout for deep analysis in seconds"
    )
    
    # Automatic Trade Execution Configuration
    auto_execute_trades: bool = Field(
        False,
        alias="AUTO_EXECUTE_TRADES",
        description="Enable automatic trade execution for confirmed recommendations"
    )
    auto_execute_min_confidence: float = Field(
        0.70,
        alias="AUTO_EXECUTE_MIN_CONFIDENCE",
        description="Minimum confidence score (0-1) to auto-execute trades",
        ge=0.0,
        le=1.0
    )
    auto_execute_position_size: float = Field(
        1000.0,
        alias="AUTO_EXECUTE_POSITION_SIZE",
        description="Default position size for automatic trades in dollars"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="allow",
        env_ignore_empty=True,  # Ignore empty string environment variables
    )

    def __init__(self, **data):
        """Initialize with better error handling for environment variables."""
        # Process list-type environment variables to ensure they're in JSON format
        env_list_fields = {
            "DEFAULT_TICKERS": "default_tickers",
            "DATA_PROVIDER_PRIORITY": "data_provider_priority", 
            "TECHNICAL_INDICATORS": "technical_indicators",
        }
        
        for env_var, _ in env_list_fields.items():
            if env_var in os.environ:
                val = os.environ[env_var].strip()
                
                # Skip empty values
                if not val:
                    del os.environ[env_var]
                    continue
                    
                # If it doesn't start with [ or {, assume it's comma-separated and convert
                if val and not val.startswith(("[", "{")):
                    # Convert comma-separated to JSON array
                    items = [item.strip() for item in val.split(",") if item.strip()]
                    os.environ[env_var] = json.dumps(items)
        
        try:
            super().__init__(**data)
        except Exception as e:
            # If it still fails, remove problematic env vars and try again
            for env_var in env_list_fields:
                if env_var in os.environ:
                    del os.environ[env_var]
            try:
                super().__init__(**data)
            except Exception:
                raise e  # Re-raise original error

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("default_tickers", mode="before")
    @classmethod
    def parse_default_tickers(cls, v) -> List[str]:
        """Parse default_tickers from various formats."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return []
            # Try JSON format first
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Try comma-separated format
            return [t.strip() for t in v.split(",") if t.strip()]
        return v

    @field_validator("data_provider_priority", mode="before")
    @classmethod
    def parse_data_provider_priority(cls, v) -> List[str]:
        """Parse data_provider_priority from various formats."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return ["yahoo"]
            # Try JSON format first
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Try comma-separated format
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator("technical_indicators", mode="before")
    @classmethod
    def parse_technical_indicators(cls, v) -> List[str]:
        """Parse technical_indicators from various formats."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return []
            # Try JSON format first
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Try comma-separated format
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

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

    def _is_valid_api_key(self, key: Optional[str]) -> bool:
        """Check if an API key is valid (not empty or a placeholder)."""
        if not key:
            return False
        key_lower = key.lower().strip()
        # Only filter out typical placeholder patterns from .env template
        # Pattern: "your_*_here" or just "your_*"
        if key_lower.startswith("your_") or key_lower.endswith("_here"):
            return False
        # Exclude common template values
        if key_lower in {"placeholder", "example", "none", "null", "xxx", "yyy", "zzz"}:
            return False
        return True

    def get_available_data_providers(self) -> List[str]:
        """Get list of data providers with valid API keys."""
        providers = []
        if self._is_valid_api_key(self.fmp_api_key):
            providers.append("fmp")
        if self._is_valid_api_key(self.polygon_api_key):
            providers.append("polygon")
        if self._is_valid_api_key(self.alpha_vantage_api_key):
            providers.append("alpha_vantage")
        if self._is_valid_api_key(self.eodhd_api_key):
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
