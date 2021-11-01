"""
All REST API Endpoints provided by Kraken according to the `specification (1.0.0)`_

This library does not provide

.. _specification (1.0.0): https://docs.kraken.com/rest/
"""
import base64
import hashlib
import hmac
import time
import urllib
from typing import List, Optional, Union

from aiohttp import ClientSession

from kraken_async_api.config import Config
from kraken_async_api.constants import Interval, Header, AssetClass, InfoType


class _RestApi:
    def __init__(self, http_session: ClientSession, config: Optional[Config] = None):
        self.http_session = http_session
        self.config = config or Config()

    async def get(self, path, **kwargs):
        """
        Perform a get request to the rest url given by :py:attr:`config`
        Keyword arguments are passed to the :class:`aiohttp.ClientSession`.

        :param path: the path to append to the rest_url and perform the request to
        :param kwargs: keyword arguments passed to the ClientSession
        :return: The result of the get call
        """
        return await self.http_session.get(self.config.rest_url + path, **kwargs)

    async def post(self, path, **kwargs):
        """
        Perform a post request to the rest url given by :py:attr:`config`
        Keyword arguments are passed to the :class:`aiohttp.ClientSession`.

        :param path: the path to append to the rest_url and perform the request to
        :param kwargs: keyword arguments passed to the ClientSession
        :return: The result of the post call
        """
        res = await self.http_session.post(self.config.rest_url + path, **kwargs)
        return await res.read()


class PublicRestApi(_RestApi):
    """
    All the publicly available endpoints according to the `Kraken specification`_

    All get methods return the results of the call they have made.

    .. _Kraken specification: https://docs.kraken.com/rest/#operation/getTickerInformation
    """

    async def get_public_endpoint(self, path, **kwargs):
        """
        Send a get request to a public Kraken endpoint given by `path`. The `path` is
        prefixed with the Kraken API url and public path provided by the config.

        This provides a way to make a specific rest call to an endpoint with
        a pre-constructed path which can include query parameters that otherwise
        may not be supported by the `get_*` methods.

        All extra keyword arguments are passed through to the :class:`aiohttp.ClientSession`.

        Example: ::

            >>> # send a get request to <Kraken API url><public path>Assets?asset=XXBT
            >>> self.get_public_endpoint("Assets?asset=XXBT")

        :param path: The unique path to a Kraken endpoint
        :param kwargs: keyword arguments passed to the ClientSession
        """
        return await super().get(self.config.public_path + path, **kwargs)

    async def get_server_time(self):
        """
        Get the server's time
        """
        return await self.get_public_endpoint("Time")

    async def get_system_status(self):
        """
        Get the current system status or trading mode.
        """
        return await self.get_public_endpoint("SystemStatus")

    async def get_asset_info(self, assets: Optional[List[str]] = None,
                             asset_class: AssetClass = AssetClass.CURRENCY):
        """
        Get information about the assets that are available for
        deposit, withdrawal, trading and staking.

        Available asset classes are given by :class:`AssetClass`.

        Examples: ::

        >>> self.get_asset_info()
        >>> self.get_asset_info(["XBT", "USD"])

        :param assets: A list of assets to get info on
        :param asset_class: The asset class. By default, 'currency'.
        """
        path = f"Assets?aclass={asset_class.value}"
        if assets:
            path += f"&asset={','.join(assets)}"
        return await self.get_public_endpoint(path)

    async def get_asset_pairs(self, pairs: Optional[List[str]] = None,
                              info: Union[InfoType, str] = InfoType.INFO):
        """
        Get asset info. Available info is given by :class:`InfoType`.

        Examples: ::

            >>> self.get_asset_pairs()
            >>> self.get_asset_pairs(["XXBTZGBP", "XXBTZUSD"], InfoType.FEES)

        :param pairs: A list of pairs to fetch info for. If not supplied, all pairs are fetched.
        :param info: The info to fetch. If not supplied, the default 'info' is used
        """
        if isinstance(info, InfoType):
            info = info.value
        path = f"AssetPairs?info={info}"
        if pairs:
            path += f"&pair={','.join(pairs)}"
        return await self.get_public_endpoint(path)

    async def get_ticker_information(self, pair: str):
        """
        Get ticket information for a given pair.

        Note: Today's prices start at midnight UTC

        Examples: ::

        >>> self.get_ticker_information("XXBTZGBP")

        :param pair: Asset pair to get data for
        """
        return await self.get_public_endpoint(f"Ticker?pair={pair}")

    async def get_ohlc_data(self, pair: str, interval: Interval = Interval.I1,
                            since: Optional[int] = None):
        """
        Get OHLC. Available interval options are given by :class:`Interval`.

        Examples: ::

            >>> self.get_ohlc_data("XXBTZGBP")
            >>> self.get_ohlc_data("XXBTZGBP", Interval.I60, since=1634045288)

        :param pair: Asset pair to get data for
        :param interval: Time frame interval in minutes
        :param since: data since a given epoch timestamp (given in seconds)
        """
        path = f"OHLC?pair={pair}&interval={interval.value}"
        if since:
            path += f"&since={since}"
        return await self.get_public_endpoint(path)

    async def get_order_book(self, pair: str, count: int = 100):
        """
        Get order book for a given pair. Count can be any integer between 1 and 500.

        Examples: ::

        >>> self.get_order_book("XXBTZGBP")
        >>> self.get_order_book("XXBTZGBP", 250)

        :param pair:  Asset pair to get data for
        :param count: maximum number of asks/bids.
        """
        return await self.get_public_endpoint(f"Depth?pair={pair}&count={count}")

    async def get_recent_trades(self, pair: str, since: Optional[Union[int, str]] = None):
        """
        Return the last trades of an asset pair. If the `since` parameter
        is not supplied, return the last 1000 trades.

        :param pair: Asset pair to get data for
        :param since: data since a given epoch timestamp (given in seconds)
        """
        return await self._get_recent("Trades", pair, since)

    async def get_recent_spreads(self, pair: str, since: Optional[Union[int, str]] = None):
        """
        Get recent spreads for a given asset pair.

        :param pair: Asset pair to get data for
        :param since: data since a given epoch timestamp (given in seconds)
        """
        return await self._get_recent("Spread", pair, since)

    async def _get_recent(self, endpoint: str, pair: str, since: Optional[Union[int, str]]):
        path = f"{endpoint}?pair={pair}"
        if since:
            path += f"&since={since}"
        return await self.get_public_endpoint(path)


class PrivateRestApi(_RestApi):
    """
    All the privately available endpoints according to the `Kraken specification`_

    All get methods return the results of the call they have made.

    For successfully calling private endpoints, the
    :attr:`Config.api_key` and :attr:`Config.api_sec` must be provided within the :class:`Config`.

    .. _Kraken specification: https://docs.kraken.com/rest/#operation/getTickerInformation
    """

    async def get_ws_token(self):
        """
        Send a post request to the Websockets Authentication endpoint
        """
        return await self.post_with_auth("GetWebSocketsToken")

    async def _get_signature(self, url_path, data):
        post_data = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + post_data).encode()
        message = url_path.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.config.api_sec), message, hashlib.sha512)
        sig_digest = base64.b64encode(mac.digest())
        return sig_digest.decode()

    async def post_with_auth(self, path, **kwargs):
        """
        Send a post request to a Kraken endpoint given by `path`, which will have the
        additional :attr:`Header.API_KEY` and :attr:`Header.API_SIGN` headers.

        :param path: The endpoint to send the request to
        """
        data = {"nonce": str(int(1000 * time.time()))}
        path = self.config.private_path + path
        headers = {Header.API_KEY: self.config.api_key,
                   Header.API_SIGN: await self._get_signature(path, data)}
        return await super().post(path, data=data, headers=headers, **kwargs)
