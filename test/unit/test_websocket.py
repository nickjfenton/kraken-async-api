import asyncio
import json
import unittest
from asyncio import Queue
from unittest.mock import AsyncMock

from websockets.legacy.client import WebSocketClientProtocol

from kraken_async_api.constants import Interval, Depth
from kraken_async_api.websocket import PublicWebSocketApi


class TestPublicWebsocket(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.mock_send = AsyncMock()
        self.callback = AsyncMock()

        self.socket = AsyncMock(WebSocketClientProtocol)
        self.socket.send = self.mock_send

        self.under_test = PublicWebSocketApi(self.callback, self.socket)

    def assert_correct_payload(self, expected_payload):
        actual_payload = self.mock_send.call_args[0][0]
        assert expected_payload == json.loads(actual_payload)

    async def test_subscribe_to_ticker(self):
        await self.under_test.subscribe_to_ticker(["XBTGBP", "XBTUSD"])

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["XBTGBP", "XBTUSD"],
            "subscription": {
                "name": "ticker"
            }
        })

    async def test_unsubscribe_from_ticker(self):
        await self.under_test.unsubscribe_from_ticker(["XBTGBP", "XBTUSD"])

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["XBTGBP", "XBTUSD"],
            "subscription": {
                "name": "ticker"
            }
        })

    async def test_subscribe_to_ohlc(self):
        await self.under_test.subscribe_to_ohlc(["foo"], Interval.I5)

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["foo"],
            "subscription": {
                "name": "ohlc",
                "interval": 5
            }
        })

    async def test_unsubscribe_from_ohlc(self):
        await self.under_test.unsubscribe_from_ohlc(["bar"], Interval.I1)

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["bar"],
            "subscription": {
                "name": "ohlc",
                "interval": 1
            }
        })

    async def test_subscribe_to_trades(self):
        await self.under_test.subscribe_to_trades(["bar"])

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["bar"],
            "subscription": {
                "name": "trade"
            }
        })

    async def test_unsubscribe_from_trades(self):
        await self.under_test.unsubscribe_from_trades(["baz"])

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["baz"],
            "subscription": {
                "name": "trade"
            }
        })

    async def test_subscribe_to_spread(self):
        await self.under_test.subscribe_to_spread(["foo"])

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["foo"],
            "subscription": {
                "name": "spread"
            }
        })

    async def test_unsubscribe_from_spread(self):
        await self.under_test.unsubscribe_from_spread(["bar"])

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["bar"],
            "subscription": {
                "name": "spread"
            }
        })

    async def test_subscribe_to_book_with_integer_depth(self):
        await self.under_test.subscribe_to_book(["hello", "motto"], depth=25)

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["hello", "motto"],
            "subscription": {
                "name": "book",
                "depth": 25
            }
        })

    async def test_subscribe_to_book_using_Depth(self):
        await self.under_test.subscribe_to_book(["test"], depth=Depth.D100)

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["test"],
            "subscription": {
                "name": "book",
                "depth": 100
            }
        })

    async def test_subscribe_to_book_without_specifying_depth(self):
        await self.under_test.subscribe_to_book(["bla"])

        self.assert_correct_payload({
            "event": "subscribe",
            "pair": ["bla"],
            "subscription": {
                "name": "book",
                "depth": 10
            }
        })

    async def test_unsubscribe_from_book_with_integer_depth(self):
        await self.under_test.unsubscribe_from_book(["hello", "motto"], depth=100)

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["hello", "motto"],
            "subscription": {
                "name": "book",
                "depth": 100
            }
        })

    async def test_unsubscribe_from_book_without_specifying_depth(self):
        await self.under_test.unsubscribe_from_book(["bla"])

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["bla"],
            "subscription": {
                "name": "book",
                "depth": 10
            }
        })

    async def test_unsubscribe_from_book_using_Depth(self):
        await self.under_test.unsubscribe_from_book(["a"], depth=Depth.D1000)

        self.assert_correct_payload({
            "event": "unsubscribe",
            "pair": ["a"],
            "subscription": {
                "name": "book",
                "depth": 1000
            }
        })

    async def test_callback_triggered_with_received_messages(self):
        asyncio.create_task(self.under_test._listen())
        queue = Queue()
        self.socket.recv = queue.get

        await queue.put("hello")
        await asyncio.sleep(0.01)

        self.callback.assert_awaited_once_with("hello")

    async def test_new_callback_is_used_after_updating(self):
        asyncio.create_task(self.under_test._listen())
        queue = Queue()
        second_callback = AsyncMock()

        # queue.get mimics the behaviour of socket.recv
        self.under_test.socket.recv = queue.get

        await queue.put("1")
        await asyncio.sleep(0.01)  # allow the created task to progress

        self.under_test.async_callback = second_callback

        await queue.put("2")
        await asyncio.sleep(0.01)

        self.callback.assert_awaited_once_with("1")
        second_callback.assert_awaited_once_with("2")


