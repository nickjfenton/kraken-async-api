import json
import time
from abc import ABC
from asyncio import Task
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, List, Coroutine, Any, Dict, TypeVar, Union

from websockets.legacy.client import WebSocketClientProtocol

from kraken_async_api.constants import Interval, Depth


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

    def __init__(self, async_callback: Callable[[str], Coroutine], socket: WebSocketClientProtocol):
        self.socket: WebSocketClientProtocol = socket
        self.async_callback: Callable = async_callback
        self.listening: Optional[Task] = None

    async def send(self, payload: dict):
        """
        A low-level method used to send a user constructed payload to the socket.

        Prefer using send_* methods, which will construct payloads for you

        :param payload: A dictionary of data to send to the endpoint
        """
        await self.socket.send(json.dumps(payload))

    async def _send_subscription(self, event, name: SubscriptionType, pair: List[str] = None,
                                 **kwargs):
        payload: Dict[str, Any] = {
            "event": event.value,
            "subscription": {
                "name": name.value,
                **kwargs
            }
        }

        if pair is not None:
            payload.update({"pair": pair})

        await self.send(payload)

    async def _listen(self):
        while True:
            message = await self.socket.recv()
            await self.async_callback(message)

    async def subscribe(self, name: SubscriptionType, pair: List[str] = None, **kwargs):
        await self._send_subscription(Event.SUBSCRIBE, name, pair, **kwargs)

    async def unsubscribe(self, name: SubscriptionType, pair: List[str] = None, **kwargs):
        await self._send_subscription(Event.UNSUBSCRIBE, name, pair, **kwargs)


class PublicWebSocketApi(_WebSocketApi):

    async def subscribe_to_ticker(self, pair: List[str]):
        """Subscribe to ticker information on currency pair."""
        await self.subscribe(PublicSubscription.TICKER, pair)

    async def unsubscribe_from_ticker(self, pair: List[str]):
        """Unsubscribe from ticker information on currency pair."""
        await self.unsubscribe(PublicSubscription.TICKER, pair)

    async def subscribe_to_book(self, pair: List[str], depth: Union[Depth, int] = Depth.D10):
        """Subscribe to order book levels. On subscription,
        a snapshot will be published at the specified depth.
        Following the snapshot, level updates will be published"""
        if isinstance(depth, Depth):
            depth = depth.value
        await self.subscribe(PublicSubscription.BOOK, pair, depth=depth)

    async def unsubscribe_from_book(self, pair: List[str], depth: Union[Depth, int] = Depth.D10):
        """Unsubscribe from order book levels."""
        if isinstance(depth, Depth):
            depth = depth.value
        await self.unsubscribe(PublicSubscription.BOOK, pair, depth=depth)

    async def subscribe_to_ohlc(self, pair: List[str], interval: Interval):
        """
        When subscribed for OHLC, a snapshot of the last valid candle (irrespective of the
        endtime) will be sent, followed by updates to the running candle. For example,
        if a subscription is made to 1 min candle and there have been no trades for 5 mins,
        a snapshot of the last 1 min candle from 5 mins ago will be published. The endtime can be
        used to determine that it is an old candle.
        """
        await self.subscribe(PublicSubscription.OHLC, pair, interval=interval.value)

    async def unsubscribe_from_ohlc(self, pair: List[str], interval: Interval):
        """
        Unsubscribe from OHLC for the given list of pairs.
        """
        await self.unsubscribe(PublicSubscription.OHLC, pair, interval=interval.value)

    async def subscribe_to_trades(self, pair: List[str]):
        """
        Trade feed for a currency pair
        """
        await self.subscribe(PublicSubscription.TRADE, pair)

    async def unsubscribe_from_trades(self, pair: List[str]):
        """
        Unsusbcribe from the trade feed for the given list of pairs
        """
        await self.unsubscribe(PublicSubscription.TRADE, pair)

    async def subscribe_to_spread(self, pair: List[str]):
        """
        Spread feed for a given list of currency pairs
        """
        await self.subscribe(PublicSubscription.SPREAD, pair)

    async def unsubscribe_from_spread(self, pair: List[str]):
        """
        Unsubscribe from spread feed for a given list of currency pairs
        """
        await self.unsubscribe(PublicSubscription.SPREAD, pair)


@dataclass
class _WsToken:
    """
    A kraken websocket authorisation token.
    This consists of the token itself, and its expiry time in seconds since Epoch
    """
    data: str
    expiry_time: Optional[int]


class PrivateWebSocketApi(_WebSocketApi):
    """
    :class:`PrivateWebSocketApi` handles Kraken private websocket connections.
    """

    def __init__(self, get_websocket_token: Callable[[], Coroutine],
                 async_callback: Callable[[str], Coroutine],
                 socket: WebSocketClientProtocol):
        super().__init__(async_callback, socket)
        self._ws_token: Optional[_WsToken] = None
        self._get_ws_token: Callable[[], Coroutine] = get_websocket_token

    async def get_ws_token(self):
        if self._ws_token is None or self._ws_token.expiry_time > int(time.time()):
            token_data = json.loads(await self._get_ws_token())
            if len(token_data["error"]) != 0:
                raise ConnectionError("Token could not be fetched. Please verify your api-key and"
                                      f" api-sec. {' '.join(token_data['error'])}")
            # Slightly reduce expiry time to account for clock sync, latency etc.
            self._ws_token = _WsToken(token_data["result"]["token"],
                                      token_data["result"]["expires"] * 0.9)
        return self._ws_token

    async def subscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.get_ws_token()
        await super().subscribe(name, pair, token=token.data, **kwargs)

    async def unsubscribe(self, name: PrivateSubscription, pair: List[str] = None, **kwargs):
        token = await self.get_ws_token()
        await super().unsubscribe(name, pair, token=token.data, **kwargs)

    async def subscribe_to_own_trades(self, **kwargs):
        """
        Own trades. On subscription last 50 trades for the user will be sent, followed by new
        trades.
        """
        await self.subscribe(PrivateSubscription.OWN_TRADES, **kwargs)

    async def unsubscribe_from_own_trades(self, **kwargs):
        await self.unsubscribe(PrivateSubscription.OWN_TRADES, **kwargs)

    async def subscribe_to_open_orders(self, **kwargs):
        """
        Open orders. Feed to show all the open orders belonging to the authenticated user.
        Initial snapshot will provide list of all open orders and then any updates to the open
        orders list will be sent. For status change updates, such as 'closed', the fields orderid
        and status will be present in the payload.
        """
        await self.subscribe(PrivateSubscription.OPEN_ORDERS, **kwargs)

    async def unsubscribe_from_open_orders(self, **kwargs):
        await self.unsubscribe(PrivateSubscription.OPEN_ORDERS, **kwargs)

    async def add_order(self, order_type: str, pair: str, price: str, side: str, volume: str,
                        **kwargs):
        """
        Add new order.
        """
        payload = {
            "event": "addOrder",
            "ordertype": order_type,
            "pair": pair,
            "price": price,
            "token": (await self.get_ws_token()).data,
            "type": side,
            "volume": volume,
            **kwargs
        }

        await self.send(payload)

    async def cancel_order(self, trade_ids: List[str]):
        """
        Cancel order or list of orders.

        For every cancelOrder message, an update message 'closeOrderStatus' is sent. For multiple
        orderid in cancelOrder, multiple update messages for 'closeOrderStatus' will be sent.

        For example, if a cancelOrder request is sent for cancelling three orders [A, B, C],
        then if two update messages for 'closeOrderStatus' are received along with an error such
        as 'EOrder: Unknown order', then it would imply that the third order is not cancelled.
        The error message could be different based on the condition which was not met by the
        'cancelOrder' request.

        :param trade_ids: A list of trade IDs for orders to cancel
        """
        payload = {
            "event": "cancelOrder",
            "token": (await self.get_ws_token()).data,
            "txid": trade_ids
        }

        await self.send(payload)

    async def cancel_all(self):
        """
        Cancel all open orders. Includes partially-filled orders.
        """
        payload = {
            "event": "cancelAll",
            "token": (await self.get_ws_token()).data
        }

        await self.send(payload)

    async def cancel_all_orders_after(self, timeout: int):
        """
        cancel_all_orders_after provides a "Dead Man's Switch" mechanism to protect the client from
        network malfunction, extreme latency or unexpected matching engine downtime. The client
        can send a request with a timeout (in seconds), that will start a countdown timer which
        will cancel *all* client orders when the timer expires. The client has to keep sending
        new requests to push back the trigger time, or deactivate the mechanism by specifying a
        timeout of 0. If the timer expires, all orders are cancelled and then the timer remains
        disabled until the client provides a new (non-zero) timeout.

        The recommended use is to make a call every 15 to 30 seconds, providing a timeout of 60
        seconds. This allows the client to keep the orders in place in case of a brief
        disconnection or transient delay, while keeping them safe in case of a network breakdown.
        It is also recommended to disable the timer ahead of regularly scheduled trading engine
        maintenance (if the timer is enabled, all orders will be cancelled when the trading
        engine comes back from downtime - planned or otherwise).
        """
        payload = {
            "event": "cancelAllOrdersAfter",
            "timeout": timeout,
            "token": (await self.get_ws_token()).data
        }

        await self.send(payload)
