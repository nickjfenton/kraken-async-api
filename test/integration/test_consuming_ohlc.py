import asyncio

from kraken_async_api import Config, Kraken


async def print_(data):
    print(f"Callback! {data}")


async def second_print(data):
    print(f"Second callable! {data}")


async def main():
    config = Config()
    kraken = await Kraken.connect(print_, config)

    await kraken.private_websocket_api.subscribe_to_open_orders()
    await asyncio.sleep(4)
    await kraken.set_callback(second_print)
    await asyncio.sleep(4)

    await kraken.close()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
