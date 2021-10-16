from typing import Callable, Optional

from aiohttp import ClientSession

from kraken_async_api.config import Config
from kraken_async_api.rest import PublicRestApi, PrivateRestApi
from kraken_async_api.websocket import PublicWebSocketApi, PrivateWebSocketApi


class Kraken:
    def __init__(self, callback: Callable,
                 http_session: Optional[ClientSession] = None,
                 config: Optional[Config] = None) -> None:

        if http_session is None:
            http_session = ClientSession()

        self.config: Config = config or Config(None, None)
        """The config used by Kraken endpoints. If no config is provided,
        default values will be used but private calls will not be possible"""

        self.public_rest = PublicRestApi(http_session, config)
        self.public_ws = PublicWebSocketApi(callback, config)

        self.private_rest = PrivateRestApi(http_session, config)
        self.private_ws = PrivateWebSocketApi(self.private_rest.get_ws_token, callback, config)

    # Add method delegates
