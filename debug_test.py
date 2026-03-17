import os

# Simulate test setup
api_keys = [
    "FMP_API_KEY", "POLYGON_API_KEY", "ALPHA_VANTAGE_API_KEY", 
    "EODHD_API_KEY", "BENZINGA_API_KEY"
]
for key in api_keys:
    if key in os.environ:
        print(f"Deleting {key}")
        del os.environ[key]

# Check if they're really deleted
print("\nAfter deletion:")
for key in api_keys:
    if key in os.environ:
        print(f"  {key} = {os.environ[key]}")
    else:
        print(f"  {key} = NOT SET")

# Now create Settings
from deerflow_openbb.config import Settings

s = Settings()
print(f"\nFMP_API_KEY from config: {s.fmp_api_key}")
print(f"Available providers: {s.get_available_data_providers()}")
print(f"Primary provider: {s.get_primary_data_provider()}")
