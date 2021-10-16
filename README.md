# --- Under development ---

# Kraken-async-api

A library for asynchronous communications with the Kraken cryptocurrency exchange.

## Quickstart

```python
from kraken_async_api import Kraken, Config

# Only necessary if you wish to communicate with private endpoints
config = Config(api_key="your api-key", api_sec="your api-sec")

kraken_exchange = Kraken(print, config=config)

kraken_exchange.public_rest.get_asset_pairs()
```
