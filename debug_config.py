#!/usr/bin/env python
from deerflow_openbb.config import Settings

try:
    s = Settings()
    print(f"log_level: {s.log_level} (expected: INFO)")
    print(f"default_llm_model: {s.default_llm_model} (expected: gpt-4)")
    print(f"redis_url: {s.redis_url}")    
    print(f"max_position_size: {s.max_position_size} (expected: 5.0)")
    print(f"default_tickers: {s.default_tickers}")
    print(f"default_tickers type: {type(s.default_tickers)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
