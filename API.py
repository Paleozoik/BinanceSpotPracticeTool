import asyncio
from time import time
from binance import AsyncClient, BinanceSocketManager
from binance.enums import KLINE_INTERVAL_1MINUTE, KLINE_INTERVAL_1HOUR
from pandas import interval_range


class API:
    client: AsyncClient
    bsm: BinanceSocketManager
    usdt_coins: list[str]
    recording: bool

    async def create_client(self, loop) -> None:
        self.client = await AsyncClient.create()
        self.bsm = BinanceSocketManager(self.client, loop)

        exchange_info = await self.client.get_exchange_info()
        self.usdt_coins = [
            x["symbol"] for x in exchange_info["symbols"] if x["symbol"].endswith("USDT")]

    async def get_price(self, symbol: str) -> float:
        symbol_ticker = await self.client.get_symbol_ticker(symbol=symbol)
        return float(symbol_ticker["price"])

    async def start_recording_price(self, symbol: str, update_price) -> None:
        self.ts = self.bsm.trade_socket(symbol)
        self.recording = True
        async with self.ts as tscm:
            while self.recording:
                res = await tscm.recv()
                update_price(res["p"])

    async def get_current_book(self, symbol: str):
        """returns bids, asks"""
        result = await self.client.get_order_book(symbol=symbol, limit=1)
        return result["bids"][0][0], result["asks"][0][0]

    async def get_kline(self, symbol: str, last_checked: int = 0) -> list:
        """
        1499040000000,      # Open time \n
        "0.01634790",       # Open \n
        "0.80000000",       # High \n
        "0.01575800",       # Low \n
        "0.01577100",       # Close \n
        "148976.11427815",  # Volume \n
        1499644799999,      # Close time \n
        "2434.19055334",    # Quote asset volume \n
        308,                # Number of trades \n
        "1756.87402397",    # Taker buy base asset volume \n
        "28.46694368",      # Taker buy quote asset volume \n
        "17928899.62484339" # Can be ignored \n
        """

        if last_checked == 0:
            result = await self.client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1MINUTE, limit=1)
        else:
            time_difference = int(time()*1000)-last_checked
            min_klines = int(time_difference/60000) + 1
            if min_klines < 500:
                result = await self.client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1MINUTE, limit = min_klines)
                print(last_checked - result[0][0])
            else:
                min_klines = int(min_klines // 60)
                result = await self.client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1HOUR, limit = min_klines)
        return result

async def main(loop: asyncio.AbstractEventLoop):
    api = API()
    await api.create_client(loop)
    await api.get_current_book("BTCUSDT")
    current_time = int(time()*1000)
    await asyncio.sleep(60)
    print(current_time)
    second_kline = await api.get_kline("BTCUSDT", current_time)
    print(second_kline)
    await asyncio.sleep(3)
    await api.client.close_connection()


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
