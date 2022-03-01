import asyncio
from API import API
from account import Account
from order import Order
from time import time


class Manager:
    """ you need to create_account, create_api, add_old_orders"""
    api: API
    account: Account
    orders: list[Order]
    live_price_task: asyncio.Task = None
    loop: asyncio.AbstractEventLoop
    app_task: asyncio.Task = None

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def create_account(self, account_info: dict) -> None:
        """Requires account_info with {"balance" : ..., "starting_balance" : ...}"""
        balance = account_info["balance"]
        starting_balance = account_info["starting_balance"]
        self.account = Account(balance, starting_balance)

    async def create_api(self) -> None:
        self.api = API()
        await self.api.create_client(self.loop)

    @staticmethod
    def order_to_dict(order: Order) -> dict:
        return {
            "buy": order.buy,
            "symbol": order.symbol,
            "ammount": order.ammount,
            "price": order.price,
            "time_placed": order.time_placed,
            "last_checked": order.last_checked
        }

    @staticmethod
    def dict_to_order(dictionary: dict) -> Order:
        """dictionary required keys: buy: bool, symbol: str, ammount: float, price: float, time_placed:int, last_checked: int"""
        new_order = Order(
            dictionary["buy"],
            dictionary["symbol"],
            dictionary["ammount"],
            dictionary["price"],
            dictionary["time_placed"],
            None,
            dictionary["last_checked"])
        return new_order

    def add_old_orders(self, orders: list[dict] = []) -> None:
        """ buy: bool, symbol: str, ammount: float, price: float, time_placed:int, last_checked: int"""
        if orders:
            self.orders = [self.dict_to_order(order) for order in orders]
        else:
            self.orders = []
        self.start_limit_loop()

    def market_order(self, buy: bool, symbol: str, ammount: float, callback) -> None:
        """callback should be of type:\n func(executed: bool, message: str)"""
        self.loop.create_task(self.create_market_order(
            buy, symbol, ammount, callback))

    async def create_market_order(self, buy: bool, symbol: str, ammount: float, callback) -> None:
        if buy:
            # check if theres enough ammount of USDT in acount
            account_ammount = self.account.get_balance_of_coin("USDT")
            price = await self.api.get_price(symbol)
            if account_ammount < ammount * price:
                callback(False, "Not enough USDT")
            self.account.withdraw("USDT", ammount*price)
            self.account.deposit(symbol.removesuffix("USDT"), ammount)
        else:
            coin = symbol.removesuffix("USDT")
            account_ammount = self.account.get_balance_of_coin(
                coin)
            price = await self.api.get_price(symbol)
            if (account_ammount < ammount):
                callback(False, f"Not enough {coin}")
            self.account.withdraw(coin, ammount)
            self.account.deposit("USDT", price*ammount)
        callback(True)

    def limit_order(self, buy: bool, symbol: str, ammount: float, order_price: float, callback) -> None:
        """callback should be of type:\n func(executed: bool, reason: str)"""
        self.loop.create_task(self.create_limit_order(
            buy, symbol, ammount, order_price, callback))

    async def create_limit_order(self, buy: bool, symbol: str, ammount: float, order_price: float, callback) -> None:
        coin = symbol.removesuffix("USDT")
        if buy:
            usdt_max = self.account.get_balance_of_coin("USDT")
            spend_ammount = order_price * ammount
            if usdt_max < spend_ammount:
                callback(False, "Not enough USDT")
                return
            # bids, asks
            current_prices = await self.api.get_current_book(symbol=symbol)
            current_price = float(current_prices[1])
            if current_price <= order_price:
                # buys at lowest ask
                spend_ammount = current_price * ammount
                self.account.withdraw("USDT", spend_ammount)
                self.account.deposit(coin, ammount)
                callback(True, "Limit buy order filled")
                return
            self.account.withdraw("USDT", spend_ammount)
            current_time = int(time() * 1000)
            new_order = Order(buy, symbol, ammount,
                              order_price, current_time, callback)
            callback(True, "Limit buy order placed")
            self.orders.append(new_order)
        else:
            usdt_max = self.account.get_balance_of_coin(coin)
            if usdt_max < ammount:
                callback(False, "Not enough USDT")
                return
            # bids, asks
            current_prices = await self.api.get_current_book(symbol=symbol)
            current_price = float(current_prices[0])
            self.account.withdraw(coin, ammount)
            if current_price >= order_price:
                # sels at highest bid
                self.account.deposit("USDT", ammount*current_price)
                callback(True, "Limit sell order filled")
                return
            current_time = int(time() * 1000)
            new_order = Order(buy, symbol, ammount,
                              order_price, current_time, callback)
            callback(True, "Limit sell order placed")
            self.orders.append(new_order)

    async def limit_order_loop(self):
        while True:
            if not len(self.orders) > 0:
                for order in self.orders:
                    order_filled = await self.check_order_filled(order)
                    if order_filled:
                        if order.buy:
                            coin = order.symbol.removesuffix("USDT")
                            self.account.deposit(coin, order.ammount)
                        else:
                            coin = "USDT"
                            self.account.deposit(coin, order.ammount * order.price)
                        order.order_filled()

                self.orders = [x for x in self.orders if not x.filled]
            await asyncio.sleep(60)

    async def check_order_filled(self, order: Order) -> bool:
        result = await self.api.get_kline(order.symbol, order.last_checked)
        for kline in result:
            if order.buy:
                if order.price >= float(kline[3]):
                    return True
            else:
                if order.price <= float(kline[2]):
                    return True
        order.last_checked = int(result[-1][6])
        return False

    def get_symbol_list(self) -> list[str]:
        return self.api.usdt_coins

    def live_price_subscribe(self, symbol: str, update_price) -> None:
        if self.live_price_task:
            self.live_price_task.cancel()
        try:
            self.live_price_task = self.loop.create_task(
                self.api.start_recording_price(symbol, update_price))
        except BaseException:
            print("live_price_subscribe failed at api.start_recording_price")

    def start_them_loops(self, updater) -> None:
        self.app_task = self.loop.create_task(updater)
        if not self.limit_order_loop_task:
            self.start_limit_loop()

    def start_limit_loop(self) -> None:
        self.limit_order_loop_task = self.loop.create_task(
            self.limit_order_loop())

    def __repr__(self) -> str:
        return f"account balance: {self.account.get_full_balance()},\ncurrent orders: {self.orders}"

    def get_account_info(self) -> str:
        balance = self.account.get_full_balance()
        return_string = "balance:\n"
        for key, value in balance.items():
            return_string = return_string + f"  {key}: {value}\n"

        if not self.orders:
            return return_string
        
        return_string = return_string + "orders:\n"
        for order in self.orders:
            buy_char = "buy" if order.buy else "sell"
            coin = order.symbol.removesuffix("USDT")
            return_string = return_string + f"  {buy_char} {coin}: {order.ammount} USDT: {order.price}\n"
        return return_string

    def get_closing_dict(self) -> dict:
        closing_dict = {"account_info": self.account.serialize_account(),
                        "old_orders": [self.order_to_dict(x) for x in self.orders]}
        return closing_dict

    def get_coin_ammount(self, coin: str) -> float:
        return self.account.get_balance_of_coin(coin)

    def on_close_start(self) -> dict:
        self.close_connection_task = self.loop.create_task(
            self.api.client.close_connection())
        if self.live_price_task:
            self.live_price_task.cancel()
        if self.app_task:
            self.app_task.cancel()
        return self.get_closing_dict()

    def on_close_end(self) -> None:
        self.loop.stop()


async def main(loop: asyncio.AbstractEventLoop) -> None:
    manager = Manager(loop)
    account_info = {"balance": {"USDT": 1000}, "starting_balance": 1000}
    manager.create_account(account_info)
    await manager.create_api()
    task = manager.create_limit_order(True, "BTCUSDT", 0.001, 38000, callback)
    manager.start_limit_loop()
    loop.create_task(task)
    order_dict = {"buy": True, "symbol": "BTCUSDT", "ammount": 1,
                  "price": 100, "time_placed": 10000000, "last_checked": 1000000}
    manager.add_old_orders([order_dict])

    # print(await manager.create_market_order(True, "SOLUSDT", 1))
    # print(manager)


def callback(*args):
    print("Callback called")
    for arg in args:
        print(arg)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()
    loop.close()
