"""Configuration objects for different Kraken Exchange environments"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """
    Config used to connect to the Kraken REST API and Websockets API.

    Default values have been provided.

    If :attr:`api_key` or :attr:`api_sec` are not given, private endpoints
    will not be reachable.
    """
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

    public_websocket_url: str = "wss://ws.kraken.com"
    """Kraken Websocket URL for querying public endpoints (ticker, ohlc, trade, spread, book)"""

    private_websocket_url: str = "wss://ws-auth.kraken.com"
    """Kraken Websocket URL for querying private endpoints"""


@dataclass
class BetaConfig(Config):
    """
    Config with default values given for the Kraken test environment.
    """
    public_websocket_url = "wss://beta-ws.kraken.com"

    private_websocket_url = "wss://beta-ws-auth.kraken.com"
