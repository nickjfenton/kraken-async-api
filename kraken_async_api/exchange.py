"""
The entrypoint to the high level API.

:class:`Kraken` manages token refreshing, and provides an API to send all
public and private Websocket messages supported by the Kraken exchange.

Messages received from the Kraken exchange are all sent back to a user provided
asynchronous callback.
"""
from typing import Callable, Coroutine, Any

from aiohttp import ClientSession
from websockets.legacy.client import connect, WebSocketClientProtocol

from kraken_async_api.config import Config
from kraken_async_api.rest import PublicRestApi, PrivateRestApi
from kraken_async_api.websocket import PublicWebSocketApi, PrivateWebSocketApi


class Kraken:
    """
    High-level API to the Kraken exchange.

    This class should be instantiated using :meth:`Kraken.connect`.

    Standard websockets usage is done through the methods of an instance
    of :class:`Kraken`. For example: ::

    >>> async def my_callback(message):
    ...     print(message)
    ...
    >>> kraken = await Kraken.connect(my_callback)
    >>> kraken.

    For lower level usage, groups of endpoints (based on whether they are REST or
    Websockets, and based on whether they require authentication) can be accessed
    through instance attributes:

    - public_rest_api
    - private_rest_api
    - public_websocket_api
    - private_websocket_api

    """
    def __init__(self,
                 async_callback: Callable,
                 public_websocket: WebSocketClientProtocol,
                 private_websocket: WebSocketClientProtocol,
                 config: Config,
                 http_session: ClientSession = None) -> None:
        self.http_session = http_session
        self.created_client_session = False
        if self.http_session is None:
            self.http_session = ClientSession()
            self.created_client_session = True

        self.public_rest_api = PublicRestApi(self.http_session, config)
        self.private_rest_api = PrivateRestApi(self.http_session, config)

        self.public_websocket_api = PublicWebSocketApi(async_callback, public_websocket)
        self.private_websocket_api = PrivateWebSocketApi(self.private_rest_api.get_ws_token,
                                                         async_callback, private_websocket)

    @classmethod
    async def connect(cls,
                      async_callback: Callable[[], Coroutine],
                      config: Config = None,
                      http_session: ClientSession = None):
        """
        Factory method to create and return a connection to the Kraken Exchange.

        Providing a config is optional. If not provided, default options will be used,
        and private endpoints will not be accessible.

        :param async_callback: the callback to use when messages are pushed to a websocket
        :param config: the Config object used to connect to the exchange
        :param http_session: The optional http session used to send REST calls
        :return: an instance of the Kraken API
        """
        config = config or Config()

        public_websocket = await connect(config.public_websocket_url)
        private_websocket = await connect(config.private_websocket_url)

        return cls(async_callback, public_websocket, private_websocket, config, http_session)

    async def set_callback(self, async_callback: Callable[[Any], Coroutine]):
        """
        Update the callback provided to the websocket clients. Messages will continue
        to be received but will be sent to the new callback.

        :param async_callback: The new asynchronous callback for the websocket clients to use
        """
        for socket in [self.public_websocket_api, self.private_websocket_api]:
            socket.async_callback = async_callback

    async def close(self):
        """
        Handle gracefully closing the connection to the Kraken exchange.
        """
        if self.created_client_session:
            await self.http_session.close()

        if self.public_websocket_api.listening:
            self.public_websocket_api.listening.cancel()
        if self.private_websocket_api.listening:
            self.private_websocket_api.listening.cancel()

        await self.public_websocket_api.socket.close()
        await self.private_websocket_api.socket.close()
