import unittest
from unittest.mock import AsyncMock

from kraken_async_api.websocket import PublicWebSocketApi


class TestPublicWebsocket(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.mock = AsyncMock()
        self.under_test = PublicWebSocketApi()
        self.under_test.send = self.mock

    async def test_subscribe_to_ticker(self):
        await self.under_test.subscribe_to_ticker(["XBTGBP", "XBTUSD"])

        print(self.mock.call_args_list)

    async def test_unsubscribe_from_ticker(self):
        assert False

    async def test_subscribe_to_ohlc(self):
        assert False

    async def test_unsubscribe_from_ohlc(self):
        assert False

    async def test_subscribe_to_trades(self):
        assert False

    async def test_unsubscribe_from_trades(self):
        assert False

    async def test_subscribe_to_spread(self):
        assert False

    async def test_unsubscribe_from_spread(self):
        assert False

    async def test_subscribe_to_book(self):
        assert False

    async def test_unsubscribe_from_book(self):
        assert False

    async def test_callback_triggered_with_received_messages(self):
        assert False
