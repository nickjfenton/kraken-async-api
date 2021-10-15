from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    api_key: Optional[str] = None
    """User generated API-Key used for authentication"""

    api_sec: Optional[str] = None
    """User generated API-Security used for authentication"""

    rest_url: str = "https://api.kraken.com"
    """Kraken base URL for REST api requests"""

    public_path: str = "/0/public/"
    """Kraken base path for public REST api calls"""

    private_path: str = "/0/private/"
    """Kraken base path for private REST api calls"""

    public_websocket_url: str = "wss://beta-ws.kraken.com"
    """Kraken Websocket URL for querying public endpoints (ticker, ohlc, trade, spread, book)"""

    private_websocket_url: str = "wss://beta-ws-auth.kraken.com"
    """Kraken Websocket URL for querying private endpoints"""
