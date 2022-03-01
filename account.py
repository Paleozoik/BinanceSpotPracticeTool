class Account:
    balance: dict[str, float]
    starting_balance: float

    def __init__(self, balance, starting_balance) -> None:
        self.balance = balance
        self.starting_balance = starting_balance

    def deposit(self, coin: str, ammount: float) -> None:
        if coin in self.balance:
            self.balance[coin] += ammount
            return
        self.balance[coin] = ammount

    def withdraw(self, coin: str, ammount: float) -> None:
        if coin not in self.balance:
            raise Exception(f"no {coin} on balance")
        if self.balance[coin] < ammount:
            raise Exception(f"not enough {coin} on balance")
        self.balance[coin] -= ammount
        if self.balance[coin] < 0.00000001:
            self.balance.pop(coin)

    def get_balance_of_coin(self, coin: str) -> float:
        if coin not in self.balance:
            return 0.0
        return self.balance[coin]

    def get_full_balance(self) -> dict[str, float]:
        return self.balance

    def serialize_account(self) -> dict:
        return {"balance": self.balance,
                "starting_balance": self.starting_balance}


if __name__ == "__main__":
    novi_account = Account({"USDT": 1000}, 1000)
