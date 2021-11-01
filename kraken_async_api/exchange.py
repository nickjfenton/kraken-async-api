"""
The entrypoint to the high level API.

:class:`Kraken` manages authentication and provides an API to send all
public and private Websocket messages supported by the Kraken exchange.
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

    Access to public and private websocket subscriptions are done through the
    `Kraken.public` and `Kraken.private` attributes. Messages can be sent via
    method calls, and messages received are passed to the client via asynchronous callbacks.

    Access to public REST endpoints are done through `Kraken.public_rest`, which can
    be used for one off querying of public exchange data. `Kraken.private_rest` can be
    used for performing authentication. REST calls are executed asynchronously, and awaiting
    their result will return the result of the REST call.

    It is recommended to prefer websockets for communicating with the exchange over
    REST calls.
    """

    def __init__(self,
                 async_callback: Callable,
                 public_websocket: WebSocketClientProtocol,
                 private_websocket: WebSocketClientProtocol,
                 config: Config,
                 http_session: ClientSession = None) -> None:

        self._http_session = http_session
        self.created_client_session = False
        if self._http_session is None:
            # if no ClientSession is given to the instance, then open one and close it on
            # Kraken.close()
            self._http_session = ClientSession()
            self.created_client_session = True

        self.public_rest = PublicRestApi(self._http_session, config)
        self.private_rest = PrivateRestApi(self._http_session, config)

        self.public = PublicWebSocketApi(async_callback, public_websocket)
        self.private = PrivateWebSocketApi(self.private_rest.get_ws_token,
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
        for socket in [self.public, self.private]:
            socket.async_callback = async_callback

    async def close(self):
        """
        Handle gracefully closing the connection to the Kraken exchange.
        """
        if self.created_client_session:
            await self._http_session.close()

        if self.public.listening:
            self.public.listening.cancel()
        if self.private.listening:
            self.private.listening.cancel()

        await self.public.socket.close()
        await self.private.socket.close()
