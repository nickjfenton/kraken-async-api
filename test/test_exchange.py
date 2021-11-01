import unittest
from unittest.mock import AsyncMock, patch, Mock

from aiohttp import ClientSession

from kraken_async_api import Kraken

mock_client_session = Mock(ClientSession)


# Patch the websockets connect function to stop actual connection attempts
@patch(target="kraken_async_api.exchange.connect", new=AsyncMock())
class TestExchange(unittest.IsolatedAsyncioTestCase):

    async def test_if_ClientSession_is_given_to_exchange_then_it_is_not_closed_on_closing_exchange_connection(self):
        # given
        http = AsyncMock()

        # when
        kraken = await Kraken.connect(AsyncMock(), config=None, http_session=http)
        await kraken.close()

        # then
        http.close.assert_not_awaited()

    async def test_if_exchange_creates_ClientSession_then_it_closes_it_on_closing_exchange_connection(self):
        with patch('kraken_async_api.exchange.ClientSession') as session_class:
            # given
            instantiated_http_session = AsyncMock()
            session_class.return_value = instantiated_http_session
            kraken = await Kraken.connect(AsyncMock(), config=None)

            # when
            await kraken.close()

            # then
            instantiated_http_session.close.assert_awaited_once()

    async def test_setting_callback_updates_all_websocket_callbacks(self):
        # given
        http = AsyncMock()
        new_callback = AsyncMock()
        kraken = await Kraken.connect(AsyncMock(), config=None, http_session=http)

        # when
        await kraken.set_callback(new_callback)

        # then
        assert kraken.public.async_callback == new_callback
        assert kraken.private.async_callback == new_callback

    async def test_closing_exchange_connection_cancels_any_listening_tasks(self):
        # given
        kraken = await Kraken.connect(AsyncMock())
        private_listening_task = Mock()
        public_listening_task = Mock()
        kraken.private.listening = private_listening_task
        kraken.public.listening = public_listening_task

        # when
        await kraken.close()

        # then
        private_listening_task.cancel.assert_called_once()
        public_listening_task.cancel.assert_called_once()
