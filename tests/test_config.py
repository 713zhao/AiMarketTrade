"""
Test suite for deerflow-openbb configuration management.
"""

import pytest

from deerflow_openbb.config import Settings, get_settings, reload_settings


def test_settings_loading():
    """Test that settings can be loaded from environment."""
    settings = Settings()
    assert settings is not None
    assert hasattr(settings, 'log_level')
    assert hasattr(settings, 'default_tickers')


def test_settings_defaults():
    """Test default values."""
    settings = Settings()
    assert settings.log_level == "INFO"
    assert settings.default_llm_model == "gpt-4"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.max_position_size == 5.0
    assert settings.default_tickers == ["AAPL", "MSFT", "GOOGL"]


def test_settings_validation():
    """Test environment variable validation."""
    import os

    # Test invalid log level
    os.environ["LOG_LEVEL"] = "INVALID"
    with pytest.raises(ValueError):
        Settings()

    # Test valid log level
    os.environ["LOG_LEVEL"] = "DEBUG"
    settings = Settings()
    assert settings.log_level == "DEBUG"

    # Clean up
    del os.environ["LOG_LEVEL"]


def test_ticker_parsing():
    """Test ticker list parsing from environment."""
    import os

    os.environ["DEFAULT_TICKERS"] = "AAPL,MSFT,GOOGL,AMZN"
    settings = Settings()
    assert settings.default_tickers == ["AAPL", "MSFT", "GOOGL", "AMZN"]

    # Test with spaces
    os.environ["DEFAULT_TICKERS"] = "AAPL, MSFT, GOOGL"
    settings = Settings()
    assert settings.default_tickers == ["AAPL", "MSFT", "GOOGL"]

    del os.environ["DEFAULT_TICKERS"]


def test_data_provider_detection():
    """Test data provider availability detection."""
    import os

    # No API keys set
    settings = Settings()
    available = settings.get_available_data_providers()
    # Should at least have yahoo
    assert "yahoo" in available

    # Add FMP key
    os.environ["FMP_API_KEY"] = "test_key_123"
    settings = Settings()
    available = settings.get_available_data_providers()
    assert "fmp" in available

    del os.environ["FMP_API_KEY"]


def test_primary_data_provider():
    """Test primary data provider selection."""
    import os

    # Start clean
    if "FMP_API_KEY" in os.environ: del os.environ["FMP_API_KEY"]
    if "POLYGON_API_KEY" in os.environ: del os.environ["POLYGON_API_KEY"]

    settings = Settings()
    # Should default to yahoo when no paid providers
    assert settings.get_primary_data_provider() == "yahoo"

    # Add FMP, should be primary
    os.environ["FMP_API_KEY"] = "test_key"
    settings = Settings()
    assert settings.get_primary_data_provider() == "fmp"

    # Add both FMP and Polygon, Polygon in priority list
    os.environ["POLYGON_API_KEY"] = "test_polygon_key"
    settings = Settings()
    # Polygon is higher priority than FMP based on default priority list
    assert settings.get_primary_data_provider() == "polygon"

    del os.environ["FMP_API_KEY"]
    del os.environ["POLYGON_API_KEY"]


def test_settings_singleton():
    """Test that get_settings returns singleton."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_reload_settings():
    """Test that reload_settings creates new instance."""
    settings1 = get_settings()
    settings2 = reload_settings()
    assert settings1 is not settings2
