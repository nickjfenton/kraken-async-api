import unittest

from kraken_async_api import PublicWebSocketApi


class TestPublicWebsocket(unittest.IsolatedAsyncioTestCase):

    def asyncSetUp(self) -> None:
        self.under_test = PublicWebSocketApi()

    async def test_subscribe_to_ticker(self):
        assert False

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
