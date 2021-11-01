import unittest
from unittest.mock import AsyncMock, Mock, patch

from aiohttp import ClientSession

from kraken_async_api.rest import PublicRestApi, PrivateRestApi
from kraken_async_api.constants import AssetClass, InfoType


class TestPublicRestApi(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.client_session = ClientSession()
        self.client_session.get = AsyncMock()
        self.client_session.post = AsyncMock()
        self.under_test = PublicRestApi(self.client_session)

    async def asyncTearDown(self) -> None:
        await self.client_session.close()

    def verify_get_call(self, url, **kwargs):
        self.client_session.get.assert_called_once_with(url, **kwargs)

    async def test_get(self):
        await self.under_test.get_public_endpoint("test?a=b&c=d", other="foo")

        self.verify_get_call('https://api.kraken.com/0/public/test?a=b&c=d', other="foo")

    async def test_get_server_time(self):
        await self.under_test.get_server_time()

        self.verify_get_call("https://api.kraken.com/0/public/Time")

    async def test_get_system_status(self):
        await self.under_test.get_system_status()

        self.verify_get_call("https://api.kraken.com/0/public/SystemStatus")

    async def test_get_asset_info_for_all_assets(self):
        await self.under_test.get_asset_info()

        self.verify_get_call("https://api.kraken.com/0/public/Assets?aclass=currency")

    async def test_get_asset_info_for_given_assets(self):
        await self.under_test.get_asset_info(["foo", "bar"])

        self.verify_get_call("https://api.kraken.com/0/public/Assets?aclass=currency&asset=foo,bar")

    async def test_get_asset_info_for_all_assets_of_a_given_class(self):
        # There is only one asset class so this test is trivial but ensures that the
        # URL is being well formed
        asset_class = Mock(AssetClass)  # Mock the Enum and use a new value
        asset_class.value = "foo"

        await self.under_test.get_asset_info(asset_class=asset_class)

        self.verify_get_call("https://api.kraken.com/0/public/Assets?aclass=foo")

    async def test_get_asset_info_for_given_assets_of_a_given_class(self):
        asset_class = Mock(AssetClass)  # Mock the Enum and use a new value
        asset_class.value = "bar"

        await self.under_test.get_asset_info(["XBT"], asset_class)

        self.verify_get_call("https://api.kraken.com/0/public/Assets?aclass=bar&asset=XBT")

    async def test_get_asset_pairs_for_all_assets(self):
        await self.under_test.get_asset_pairs()

        self.verify_get_call("https://api.kraken.com/0/public/AssetPairs?info=info")

    async def test_get_asset_pairs_for_given_assets(self):
        await self.under_test.get_asset_pairs(["XXBTZGBP", "XXBTZUSD"])

        self.verify_get_call(
            "https://api.kraken.com/0/public/AssetPairs?info=info&pair=XXBTZGBP,XXBTZUSD"
        )

    async def test_get_asset_pairs_at_given_info_level(self):
        await self.under_test.get_asset_pairs(["XXBTZGBP"], InfoType.FEES)

        self.verify_get_call(
            "https://api.kraken.com/0/public/AssetPairs?info=fees&pair=XXBTZGBP"
        )

    async def test_get_asset_pairs_at_given_string_info_level(self):
        await self.under_test.get_asset_pairs(["XXBTZGBP"], "foo")

        self.verify_get_call(
            "https://api.kraken.com/0/public/AssetPairs?info=foo&pair=XXBTZGBP"
        )

    async def test_get_ticker_information_for_a_given_asset_pair(self):
        await self.under_test.get_ticker_information("XBTGBP")

        self.verify_get_call("https://api.kraken.com/0/public/Ticker?pair=XBTGBP")

    async def test_get_ohlc_data_for_a_given_asset_pair(self):
        await self.under_test.get_ohlc_data("foo")

        self.verify_get_call("https://api.kraken.com/0/public/OHLC?pair=foo&interval=1")

    async def test_get_ohlc_data_since_a_given_time(self):
        await self.under_test.get_ohlc_data("XBTGBP", since=123)

        self.verify_get_call(
            "https://api.kraken.com/0/public/OHLC?pair=XBTGBP&interval=1&since=123"
        )

    async def test_get_order_book_for_a_given_asset_pair(self):
        await self.under_test.get_order_book("XBT")

        self.verify_get_call("https://api.kraken.com/0/public/Depth?pair=XBT&count=100")

    async def test_get_recent_trades_for_a_given_asset_pair(self):
        await self.under_test.get_recent_trades("bar")

        self.verify_get_call("https://api.kraken.com/0/public/Trades?pair=bar")

    async def test_get_recent_trades_for_a_given_asset_pair_since_a_given_time(self):
        await self.under_test.get_recent_trades("foo", 123)

        self.verify_get_call("https://api.kraken.com/0/public/Trades?pair=foo&since=123")

    async def test_get_recent_spreads_for_a_given_asset_pair(self):
        await self.under_test.get_recent_spreads("abc")

        self.verify_get_call("https://api.kraken.com/0/public/Spread?pair=abc")

    async def test_get_recent_spreads_for_a_given_asset_pair_since_a_given_time(self):
        await self.under_test.get_recent_spreads("abc", 456)

        self.verify_get_call("https://api.kraken.com/0/public/Spread?pair=abc&since=456")

    async def test_calls_are_made_to_the_rest_url_supplied_by_the_config(self):
        self.under_test.config.rest_url = "foo"

        await self.under_test.get_public_endpoint("some_path")

        self.verify_get_call("foo/0/public/some_path")

    async def test_calls_are_made_to_the_public_path_supplied_by_the_config(self):
        self.under_test.config.public_path = "/bla/"

        await self.under_test.get_public_endpoint("new_path?foo=bar")

        self.verify_get_call("https://api.kraken.com/bla/new_path?foo=bar")


# Patch time.time() which is used for the nonce and api-sign
@patch(target="time.time", new=lambda: 5)
class TestPrivateRest(unittest.IsolatedAsyncioTestCase):

    # NOTE: The below tested methods were manually verified to work using an actual API-SEC and
    # API-Key. On this basis, the unit tests were added afterwards with a fake api-sec and api-key
    # and the resultant api-sign that was generated has been used in these tests to confirm that
    # in the event of any refactor, given the same (fake) api-key, api-sec, and nonce, the calls
    # should still generate the same api-sign as below.

    async def asyncSetUp(self) -> None:
        self.client_session = Mock(ClientSession)
        self.client_session.get = AsyncMock()
        self.client_session.post = AsyncMock()
        self.under_test = PrivateRestApi(self.client_session)
        self.under_test.config.api_key = "abc"
        self.under_test.config.api_sec = "123="

    async def asyncTearDown(self) -> None:
        await self.client_session.close()

    def check_post_call(self, url, api_sign, **kwargs):
        data = {"nonce": "5000"}  # Patched time.time() returns 5
        headers = {"API-KEY": "abc",
                   "API-Sign": api_sign}
        self.client_session.post.assert_called_once_with(url, data=data, headers=headers, **kwargs)

    async def test_calls_are_made_to_the_rest_url_supplied_by_the_config(self):
        self.under_test.config.rest_url = "bar"
        await self.under_test.post_with_auth("Balance")

        self.check_post_call("bar/0/private/Balance",
                             "3SwKsOrZPBX3YSG1Bkh6EWTPcE2UPFNsNBIx"
                             "/j2PZnLYHpsbsNYciDNDnmmg6QAuw2uxAIYO8a7xjryWfXvEMA==")

    async def test_get_ws_token(self):
        await self.under_test.get_ws_token()

        self.check_post_call("https://api.kraken.com/0/private/GetWebSocketsToken",
                             "HB54iWkvRJhBAzVz6EzvWLllGfguM9wKlsG1gQj6WLvYTAlAoVY1s"
                             "I9RFBbXidaregrNOxys9MDqpa+5aATRlQ==")

    async def test_error_raised_if_api_key_missing(self):
        # given
        self.under_test.config.api_key = None
        error_msg = "Complete config has not been provided. Please supply a Kraken API-KEY and " \
                    "API-SEC."

        # when/then
        with self.assertRaisesRegex(ConnectionError, error_msg):
            await self.under_test.post_with_auth("/")

    async def test_error_raised_if_api_sec_missing(self):
        # given
        self.under_test.config.api_sec = None
        error_msg = "Complete config has not been provided. Please supply a Kraken API-KEY and " \
                    "API-SEC."

        # when/then
        with self.assertRaisesRegex(ConnectionError, error_msg):
            await self.under_test.post_with_auth("/")
