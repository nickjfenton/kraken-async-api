import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, List, Coroutine, Any, Dict, TypeVar

from websockets.legacy.client import WebSocketClientProtocol, connect

from kraken_async_api.config import Config
from kraken_async_api.util import no_op


class Event(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"


class Message(Enum):
    pass


class Subscription(Message):
    pass


SubscriptionType = TypeVar("SubscriptionType", bound=Subscription)


class PublicMessage(Message):
    pass


class PublicSubscription(Subscription):
    TICKER = "ticker"
    OHLC = "ohlc"
    TRADE = "trade"
    SPREAD = "spread"
    BOOK = "book"


class PrivateMessage(Message):
    ADD_ORDER = "addOrder"
    CANCEL_ORDER = "cancelOrder"
    CANCEL_ALL = "cancelAll"
    CANCEL_ALL_ORDERS_AFTER = "cancelAllOrdersAfter"


class PrivateSubscription(Subscription):
    OPEN_ORDERS = "openOrders"
    OWN_TRADES = "ownTrades"


class _WebSocketApi(ABC):

    def __init__(self, callback: Optional[Callable[[str], Any]] = None,
                 config: Optional[Config] = None):
        self.config = config or Config()
        self.socket: Optional[WebSocketClientProtocol] = None
        self.callback: Callable = callback or no_op

    @property
    @abstractmethod
    def _url(self) -> str:
        """The websockets URL to use"""

    async def send(self, payload: dict):
        """
        A low-level method used to send a user constructed payload to the socket.

        Prefer using send_* methods, which will construct payloads for you

        :param payload: A dictionary of data to send to the endpoint
        """
        socket = await self._get_connected_websocket()

        await socket.send(payload)

    async def _send_message(self, event, payload: Optional[Dict] = None):
        if payload is None:
            payload = {}
        payload.update({"event": event})
        await self.send(payload)

    async def send_ping(self, req_id: Optional[int]):
        if req_id is not None:
            await self._send_message(Event.PING, {"reqid": req_id})
        else:
            await self._send_message(Event.PING)

    async def send_subscription(self, event, name: SubscriptionType, pair: List[str] = None,
                                **kwargs):
        payload: Dict[str, Any] = {
            "subscription": {
                "name": name.value,
                **kwargs
            }
        }

        if pair is not None:
            payload.update({"pair": pair})

        await self._send_message(event, payload)

    async def _get_connected_websocket(self) -> WebSocketClientProtocol:
        if self.socket is None:
            self.socket = await connect(self._url)
            asyncio.create_task(self._listen())
        return self.socket

    async def _listen(self):
        while True:
            response = await self.socket.recv()
            self.callback(response)

    async def subscribe(self, name: SubscriptionType, pair: List[str] = None, **kwargs):
        await self.send_subscription(Event.SUBSCRIBE, name, pair, **kwargs)

    async def unsubscribe(self, name: Subscription, pair: List[str] = None, **kwargs):
        await self.send_subscription(Event.UNSUBSCRIBE, name, pair, **kwargs)


class PublicWebSocketApi(_WebSocketApi):

    @property
    def _url(self) -> str:
        return self.config.public_websocket_url

    async def subscribe(self, name: PublicSubscription, pair: List[str] = None, **kwargs):
        """
        Send a subscription event to the websocket.

        Prefer subscribe_to_* methods.
        """
        await super().subscribe(name, pair, **kwargs)

    async def subscribe_to_ticker(self, pair: List[str]):
        """Subscribe to ticker information on currency pair."""
        await self.subscribe(PublicSubscription.TICKER, pair)

    async def unsubscribe_from_ticker(self, pair: List[str]):
        """Unsubscribe from ticker information on currency pair."""
        await self.unsubscribe(PublicSubscription.TICKER, pair)

    async def subscribe_to_book(self, pair: List[str]):
        """Subscribe to order book levels. On subscription,
        a snapshot will be published at the specified depth.
        Following the snapshot, level updates will be published"""
        await self.subscribe(PublicSubscription.BOOK, pair)

    async def unsubscribe_from_book(self, pair: List[str]):
        """Unsubscribe from order book levels."""
        await self.unsubscribe(PublicSubscription.BOOK, pair)


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
    :class:`PrivateWebSocketApi` handles Kraken private websocket connections.
    """

    def __init__(self, get_websocket_token: Callable,
                 callback: Optional[Callable[[str], Any]] = None,
                 config: Optional[Config] = None):
        super().__init__(callback, config)
        self._ws_token: Optional[_WsToken] = None
        self._get_ws_token: Callable[[], Coroutine] = get_websocket_token

    @property
    def _url(self) -> str:
        return self.config.private_websocket_url

    async def get_ws_token(self):
        if self._ws_token is None or self._ws_token.expiry_time > int(time.time()):
            self._ws_token = await self._get_ws_token()
        return self._ws_token

    async def subscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.get_ws_token()
        await super().subscribe(name, pair, token=token, **kwargs)

    async def unsubscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.get_ws_token()
        await super().unsubscribe(name, pair, token=token, **kwargs)

    async def subscribe_to_own_trades(self, **kwargs):
        await self.subscribe(PrivateSubscription.OWN_TRADES, **kwargs)

    async def unsubscribe_from_own_trades(self, **kwargs):
        await self.unsubscribe(PrivateSubscription.OWN_TRADES, **kwargs)

    async def subscribe_to_open_orders(self, **kwargs):
        await self.subscribe(PrivateSubscription.OPEN_ORDERS, **kwargs)

    async def unsubscribe_from_open_orders(self, **kwargs):
        await self.unsubscribe(PrivateSubscription.OPEN_ORDERS, **kwargs)

    async def add_order(self, order_type: str, pair: str, price: str, side: str, volume: str,
                        **kwargs):
        payload = {
            "event": "addOrder",
            "ordertype": order_type,
            "pair": pair,
            "price": price,
            "token": await self.get_ws_token(),
            "type": side,
            "volume": volume,
            **kwargs
        }

        await self.send(payload)

    async def cancel_order(self, trade_ids: List[str]):
        payload = {
            "event": "cancelOrder",
            "token": await self.get_ws_token(),
            "txid": trade_ids
        }

        await self.send(payload)

    async def cancel_all(self):
        payload = {
            "event": "cancelAll",
            "token": await self.get_ws_token()
        }

        await self.send(payload)

    async def cancel_all_orders_after(self, timeout: int):
        payload = {
            "event": "cancelAllOrdersAfter",
            "timeout": timeout,
            "token": await self.get_ws_token()
        }

        await self.send(payload)
