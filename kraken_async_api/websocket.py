import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, List, Coroutine

from websockets.legacy.client import WebSocketClientProtocol, connect

from kraken_async_api.config import Config


class Event(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class Subscription(Enum):
    pass


class PublicSubscription(Subscription):
    book = "book"
    ticker = "ticker"


class PrivateSubscription(Subscription):
    open_orders = "openOrders"
    own_trades = "ownTrades"


class _WebSocketApi(ABC):

    def __init__(self, config: Config, callback: Optional[Callable]):
        self.config = config
        self.socket: Optional[WebSocketClientProtocol] = None
        self.callback: Callable = callback or self.no_op

    def no_op(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def _url(self) -> str:
        """The websockets URL to use"""

    async def send(self, event, name: Subscription, pair: List[str] = None, **kwargs):
        ws = await self._get_connected_websocket()

        payload = {
            "event": event,
            "subscription": {
                "name": name,
                **kwargs
            }
        }

        if pair is not None:
            payload.update({"pair": pair})

        await ws.send(payload)

    async def _get_connected_websocket(self) -> WebSocketClientProtocol:
        if self.socket is None:
            self.socket = await connect(self._url)
            asyncio.create_task(self._listen())
        return self.socket

    async def _listen(self):
        while True:
            response = await self.socket.recv()
            self.callback(response)

    async def subscribe(self, name: Subscription, pair: List[str] = None, **kwargs):
        await self.send(Event.SUBSCRIBE, name, pair, **kwargs)

    async def unsubscribe(self, name: Subscription, pair: List[str] = None, **kwargs):
        await self.send(Event.UNSUBSCRIBE, name, pair, **kwargs)


class PublicWebSocketApi(_WebSocketApi):

    @property
    def _url(self) -> str:
        return self.config.public_websocket_url

    class Name(Enum):
        ticker = "ticker"
        book = "book"

    async def subscribe(self, name: PublicSubscription, pair: List[str] = None, **kwargs):
        await super().subscribe(name, pair, **kwargs)

    async def subscribe_to_ticker(self, pair):
        await self.subscribe(PublicSubscription.ticker, pair)

    async def unsubscribe_from_ticker(self, pair):
        await self.unsubscribe(PublicSubscription.ticker, pair)

    async def subscribe_to_book(self, pair):
        await self.subscribe(PublicSubscription.book, pair)

    async def unsubscribe_from_book(self, pair):
        await self.unsubscribe(PublicSubscription.book, pair)


@dataclass
class _WsToken:
    """
    A kraken websocket authorisation token.
    This consists of the token itself, and its expiry time in seconds since Epoch
    """
    token: str
    expiry_time: Optional[int]


class PrivateWebSocketApi(_WebSocketApi):
    """
    :class:`PrivateWebSocketApi` handles connecting
    """
    def __init__(self, config: Config, callback: Optional[Callable], get_websocket_token: Callable):
        super().__init__(config, callback)
        self._ws_token: Optional[_WsToken] = None
        self.get_ws_token: Callable[[], Coroutine[str]] = get_websocket_token

    @property
    def _url(self) -> str:
        return self.config.private_websocket_url

    @property
    async def ws_token(self) -> _WsToken:
        if self._ws_token is not None:
            if self._ws_token.expiry_time is None or self._ws_token.expiry_time > int(time.time()):
                return self._ws_token
            if self.get_ws_token:
                self._ws_token = await self.get_ws_token()
        return self._ws_token

    async def subscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.ws_token
        await super().subscribe(name, pair, token=token, **kwargs)

    async def unsubscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.ws_token
        await super().unsubscribe(name, pair, token=token, **kwargs)

    async def subscribe_to_own_trades(self, **kwargs):
        await self.subscribe(PublicSubscription.own_trades, **kwargs)

    async def subscribe_to_open_orders(self, **kwargs):
        await self.subscribe(PublicSubscription.open_orders, **kwargs)
