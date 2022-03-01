class Order:
    buy: bool
    symbol: str
    ammount: float
    price: float
    time_placed: int
    last_checked: int

    def __init__(self, buy:bool, symbol:str, ammount:float, price:float, time_placed:int, callback = None, last_checked: int = 0) -> None:
        self.buy = buy
        self.symbol = symbol
        self.ammount = ammount
        self.price = price
        self.time_placed = time_placed
        self.last_checked = time_placed if last_checked == 0 else last_checked
        self.callback = callback
        self.filled = False

    def order_filled(self) -> None:
        if self.callback:
            self.callback(True, f"{self.symbol} order filled")
        self.filled = True

    def call_the_callback(self, executed: bool, reason: str = None) -> None:
        """args are filled: bool, and message: str"""
        if (self.callback):
            if reason:
                self.callback(executed, reason)
            else:
                self.callback(executed)

    def __repr__(self) -> str:
        buy = "buy" if self.buy else "sell"

        return f"{buy}, {self.symbol}, {self.time_placed}"