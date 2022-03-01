import asyncio
import tkinter as tk
import tkinter.ttk as ttk
from aid import Aid
from manager import Manager
import tkinter.scrolledtext as sc
import json


class TestAPP(tk.Tk):
    manager: Manager
    symbol_list: list[str]
    current_symbol: str
    current_price: str = "0"

    market_change = True
    error_decounter = 0

    hacky_workaround = False

    def __init__(self, manager: Manager, closer=None) -> None:
        super().__init__()
        
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.closer = closer
        self.manager = manager
        self.symbol_list = manager.get_symbol_list()

        self.current_symbol = None
        self.create_gui()
        self.manager.start_them_loops(updater=self.updater(1/60))

    def create_gui(self) -> None:
        HEIGHT = 800
        WIDTH = 600

        self.canvas = tk.Canvas(self, height=HEIGHT, width=WIDTH, bg="#1c1b22")
        self.canvas.pack()

        #self.debug_label.grid(row = 0, column=1, columnspan=3)

        self.create_trading_frame()
        self.create_account_frame()

        s = ttk.Style(self.trading_frame)
        s.theme_use("clam")

    def create_trading_frame(self) -> None:
        self.trading_frame = tk.Frame(
            self,
            # bg="#161a1e"
        )
        self.trading_frame.place(relwidth=1, relheight=0.7)

        self.naslov = tk.Label(
            self.trading_frame,
            text="Binance trading test app"
        )
        self.naslov.grid(row=0, column=0, columnspan=2)

        self.debug_label = tk.Label(self.trading_frame, text="...")
        self.debug_label.grid(row=0, column=2, columnspan=2)

        self.selected_value = tk.StringVar(self)
        self.selected_value.set("Select a coin")
        self.symbolMenu = tk.OptionMenu(
            self.trading_frame,
            self.selected_value,
            *self.symbol_list,
            command=self.symbol_changed
        )
        self.symbolMenu.grid(row=1, column=0)

        self.price_label = tk.Label(
            self.trading_frame,
            text="Price"
        )
        self.price_label.grid(row=1, column=1, sticky="E")

        self.current_price_label = tk.Label(
            self.trading_frame,
            text="###"
        )
        self.current_price_label.grid(row=1, column=2, sticky="E")

        self.usdt_suffix = tk.Label(
            self.trading_frame,
            text="USDT"
        )
        self.usdt_suffix.grid(row=1, column=3, sticky="W")

        # <<< market_order >>>

        self.market_label = tk.Label(
            self.trading_frame,
            text="Market order"
        )
        self.market_label.grid(row=2, column=0)

        self.market_quantity_label = tk.Label(
            self.trading_frame,
            text=f"Ammount COIN"
        )
        self.market_quantity_label.grid(row=3, column=1)

        self.market_coin_quantity_string = tk.StringVar()
        self.market_coin_quantity_string.trace_add(
            "write", self.market_coin_quantity_changed)

        self.market_coin_quantity_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.market_coin_quantity_string,
            selectbackground="#e0e0ff"
        )
        self.market_coin_quantity_entry.grid(row=3, column=2)

        self.market_price_label = tk.Label(
            self.trading_frame,
            text=f"Ammount USDT"
        )
        self.market_price_label.grid(row=3, column=3)

        self.market_USDT_quantity_string = tk.StringVar()
        self.market_USDT_quantity_string.trace_add(
            "write", self.market_USDT_quantity_changed)
        self.market_price_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.market_USDT_quantity_string
        )
        self.market_price_entry.grid(row=3, column=4)

        self.market_buy_button = tk.Button(
            self.trading_frame,
            text="Buy",
            bg="#0ecb83",
            command=self.market_buy_button_pressed
        )
        self.market_buy_button.grid(row=4, column=1, columnspan=2, ipadx=70)

        self.market_sell_button = tk.Button(
            self.trading_frame,
            text="Sell",
            bg="#f6465d",
            command=self.market_sell_button_pressed
        )
        self.market_sell_button.grid(row=4, column=3, columnspan=2, ipadx=70)

        # <<< limit_order >>>

        self.limit_label = tk.Label(
            self.trading_frame,
            text="Limit order"
        )
        self.limit_label.grid(row=5, column=0)
        self.limit_buy_price_label = tk.Label(
            self.trading_frame,
            text="Price"
        )
        self.limit_buy_price_label.grid(row=6, column=1)
        self.limit_buy_price_string = tk.StringVar()
        limit_buy_price_changed_command = self.register(
            self.limit_buy_price_changed)
        self.limit_buy_price_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_buy_price_string,
            validatecommand=(limit_buy_price_changed_command, "%d", "%P"),
            validate="key"
        )
        self.limit_buy_price_entry.grid(row=6, column=2)

        self.limit_buy_ammount_label = tk.Label(
            self.trading_frame,
            text="Ammount"
        )
        self.limit_buy_ammount_label.grid(row=7, column=1)
        self.limit_buy_ammount_string = tk.StringVar()
        limit_buy_ammount_changed_command = self.register(
            self.limit_buy_ammount_changed)
        self.limit_buy_ammount_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_buy_ammount_string,
            validatecommand=(limit_buy_ammount_changed_command, '%d', '%P'),
            validate="key"
        )
        self.limit_buy_ammount_entry.grid(row=7, column=2)

        self.limit_buy_decrement_price = tk.Button(
            self.trading_frame,
            text="-1%",
            command=self.limit_buy_decrement_pressed
        )
        self.limit_buy_decrement_price.grid(
            row=8, column=1, columnspan=2, sticky="W", ipadx=10)

        self.limit_buy_zero_price = tk.Button(
            self.trading_frame,
            text=" 0%",
            command=self.limit_buy_zero_pressed
        )
        self.limit_buy_zero_price.grid(row=8, column=1, columnspan=2, ipadx=10)

        self.limit_buy_increment_price = tk.Button(
            self.trading_frame,
            text="+1%",
            command=self.limit_buy_increment_pressed
        )
        self.limit_buy_increment_price.grid(
            row=8, column=1, columnspan=2, sticky="E", ipadx=10)

        self.limit_buy_total_label = tk.Label(
            self.trading_frame,
            text="Total"
        )
        self.limit_buy_total_label.grid(row=9, column=1)
        self.limit_buy_total_string = tk.StringVar()
        limit_sell_total_changed_command = self.register(
            self.limit_buy_total_changed)
        self.limit_buy_total_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_buy_total_string,
            validatecommand=(limit_sell_total_changed_command, "%d", "%P"),
            validate="key"
        )
        self.limit_buy_total_entry.grid(row=9, column=2)

        self.limit_buy_button = tk.Button(
            self.trading_frame,
            text="Buy",
            bg="#0ecb83",
            command=self.limit_buy_button_pressed
        )
        self.limit_buy_button.grid(row=10, column=1, columnspan=2, ipadx=70)

        self.limit_sell_price_label = tk.Label(
            self.trading_frame,
            text="Price"
        )
        self.limit_sell_price_label.grid(row=6, column=3)

        self.limit_sell_price_string = tk.StringVar()
        limit_sell_price_changed_command = self.register(
            self.limit_sell_price_changed)
        self.limit_sell_price_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_sell_price_string,
            validatecommand=(limit_sell_price_changed_command, "%d", "%P"),
            validate="key"
        )
        self.limit_sell_price_entry.grid(row=6, column=4)

        self.limit_sell_ammount_label = tk.Label(
            self.trading_frame,
            text="Ammount"
        )
        self.limit_sell_ammount_label.grid(row=7, column=3)

        self.limit_sell_ammount_string = tk.StringVar()
        limit_sell_ammount_changed_command = self.register(
            self.limit_sell_ammount_changed)
        self.limit_sell_ammount_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_sell_ammount_string,
            validatecommand=(limit_sell_ammount_changed_command, '%d', '%P'),
            validate="key"
        )
        self.limit_sell_ammount_entry.grid(row=7, column=4)

        self.limit_sell_decrement_price = tk.Button(
            self.trading_frame,
            text="-1%",
            command=self.limit_sell_decrement_pressed
        )
        self.limit_sell_decrement_price.grid(
            row=8, column=3, columnspan=2, sticky="W", ipadx=10)

        self.limit_sell_zero_price = tk.Button(
            self.trading_frame,
            text=" 0%",
            command=self.limit_sell_zero_pressed
        )
        self.limit_sell_zero_price.grid(
            row=8, column=3, columnspan=2, ipadx=10)

        self.limit_sell_increment_price = tk.Button(
            self.trading_frame,
            text="+1%",
            command=self.limit_sell_increment_pressed
        )
        self.limit_sell_increment_price.grid(
            row=8, column=3, columnspan=2, sticky="E", ipadx=10)

        self.limit_sell_total_label = tk.Label(
            self.trading_frame,
            text="Total"
        )
        self.limit_sell_total_label.grid(row=9, column=3)
        self.limit_sell_total_string = tk.StringVar()
        limit_sell_total_changed_command = self.register(
            self.limit_sell_total_changed)
        self.limit_sell_total_entry = tk.Entry(
            self.trading_frame,
            textvariable=self.limit_sell_total_string,
            validatecommand=(limit_sell_total_changed_command, "%d", "%P"),
            validate="key"
        )
        self.limit_sell_total_entry.grid(row=9, column=4)

        self.limit_sell_button = tk.Button(
            self.trading_frame,
            text="Sell",
            bg="#f6465d",
            command=self.limit_sell_button_pressed
        )
        self.limit_sell_button.grid(row=10, column=3, columnspan=2, ipadx=70)

    def create_account_frame(self) -> None:
        self.account_frame = tk.Frame(self, bg="#f6fafe")
        self.account_frame.place(relwidth=1, relheight=0.3, rely=0.7)
        self.random_button = tk.Button(
            self.account_frame,
            text="account frame",
            command=self.random_button_pressed
        )
        self.random_button.grid(row=0)
        self.account_info_scrollable = sc.ScrolledText(self.account_frame)
        self.account_info_scrollable.grid(row=1)
        self.account_info_scrollable.config(state="disabled")

    def market_coin_quantity_changed(self, *args) -> None:
        self.market_change = not self.market_change
        if self.market_change:
            return
        try:
            value = float(self.market_coin_quantity_string.get())
            current_price = float(self.current_price)
            self.market_coin_quantity_string.set(Aid.round_to_5_sig_fig(value))
            self.market_USDT_quantity_string.set(
                Aid.round_to_5_sig_fig(value * current_price))
        except:
            self.report_error("error market_coin")
            self.market_coin_quantity_string.set("0.0")
            self.market_USDT_quantity_string.set("0.0")

    def market_USDT_quantity_changed(self, *args) -> None:
        self.market_change = not self.market_change
        if self.market_change:
            return
        try:
            value = float(self.market_USDT_quantity_string.get())
            current_price = float(self.current_price)
            self.market_coin_quantity_string.set(
                Aid.round_to_5_sig_fig(value / current_price))
            self.market_USDT_quantity_string.set(Aid.round_to_5_sig_fig(value))
        except:
            self.report_error("error market_USDT")
            self.market_coin_quantity_string.set("0.0")
            self.market_USDT_quantity_string.set("0.0")

    def market_buy_button_pressed(self, *args) -> None:
        try:
            ammount = float(self.market_coin_quantity_entry.get())
        except:
            self.report_error("couldn't get coin ammount")
        if ammount:
            self.manager.market_order(
                True, self.current_symbol, ammount, self.market_order_callback)

    def market_sell_button_pressed(self, *args) -> None:
        try:
            ammount = float(self.market_coin_quantity_entry.get())
        except:
            self.report_error("couldn't get coin ammount")
        if ammount:
            self.manager.market_order(
                False, self.current_symbol, ammount, self.market_order_callback)

    def market_order_callback(self, executed: bool, reason: str = "") -> None:
        if executed:
            self.report_success("Market order success")
        else:
            self.report_error(reason)

    # <<< Limit widgets >>>

    def limit_buy_price_changed(self, callback_code: str, limit_price: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_price = float(limit_price)
        except:
            self.limit_order_callback(
                False, "I don't understand your limit price")
            return True
        try:
            limit_ammount = self.limit_buy_ammount_entry.get()
            limit_ammount = float(limit_ammount)
        except:
            print("limit_ammount is problem")
            return True

        if type(limit_price) is float and type(limit_ammount) is float:
            limit_total = limit_ammount * limit_price
            self.limit_buy_total_string.set(
                Aid.round_to_5_sig_fig(limit_total))
        return True

    def limit_buy_ammount_changed(self, callback_code: str, limit_ammount: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_ammount = float(limit_ammount)
        except:
            self.limit_order_callback(False, "limit_ammount is not a float")
            return True

        try:
            limit_price = self.limit_buy_price_entry.get()
            limit_price = float(limit_price)
        except:
            print("limit_prince is problem")
            return True

        coin = "USDT"
        coin_balance = self.manager.get_coin_ammount(coin)

        # checks if there's enough USDT on your account

        if coin_balance < limit_ammount * limit_price:
            if limit_price == 0:
                print("limit price")
                return True
            limit_ammount = coin_balance / limit_price
            self.hack_workaround(
                "limit_buy_ammount", Aid.round_to_5_sig_fig(limit_ammount))
            self.limit_order_callback(
                False, "limit ammount set to max ammount")
        limit_total = limit_ammount*limit_price
        self.limit_buy_total_string.set(Aid.round_to_5_sig_fig(limit_total))
        return True

    def limit_buy_total_changed(self, callback_code: str, limit_total: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_total = float(limit_total) if limit_total != "" else None
        except:
            self.limit_order_callback(
                False, "I don't understand limit total")
            return True

        try:
            limit_price = self.limit_buy_price_entry.get()
            limit_price = float(limit_price)
        except:
            print("limit_ammount is a problem")
            return True

        coin = "USDT"
        coin_balance = self.manager.get_coin_ammount(coin)

        if coin_balance < limit_total:
            limit_total = coin_balance
            value = "{:.2f}".format(limit_total)
            self.hack_workaround("limit_buy_total", value)
            self.limit_order_callback(
                False, "limit total set to max")

        if limit_price == 0:
            return True
        limit_ammount = limit_total/limit_price
        self.limit_buy_ammount_string.set(
            Aid.round_to_5_sig_fig(limit_ammount))
        return True

    def limit_buy_decrement_pressed(self, *args) -> None:
        try:
            current_price = self.limit_buy_price_entry.get()
            current_price = float(current_price)
        except:
            print("can't understand price")
            return
        new_price = current_price * 0.99
        self.limit_buy_price_string.set(Aid.round_to_5_sig_fig(new_price))
        self.limit_buy_price_changed("1", Aid.round_to_5_sig_fig(new_price))

    def limit_buy_zero_pressed(self, *args) -> None:
        try:
            current_price = self.current_price
            current_price = float(current_price)
        except:
            print("can't understand current price")
            return
        self.limit_buy_price_string.set(Aid.round_to_5_sig_fig(current_price))
        self.limit_buy_price_changed(
            "1", Aid.round_to_5_sig_fig(current_price))

    def limit_buy_increment_pressed(self, *args) -> None:
        try:
            current_price = self.limit_buy_price_entry.get()
            current_price = float(current_price)
        except:
            print("can't understand price")
            return
        new_price = current_price * 1.01
        self.limit_buy_price_string.set(Aid.round_to_5_sig_fig(new_price))
        self.limit_buy_price_changed("1", Aid.round_to_5_sig_fig(new_price))

    def limit_buy_button_pressed(self, *args) -> None:
        limit_price = float(self.limit_buy_price_string.get())
        limit_ammount = float(self.limit_buy_ammount_string.get())
        self.manager.limit_order(
            True, self.current_symbol, limit_ammount, limit_price, self.limit_order_callback)

    def limit_sell_price_changed(self, callback_code: str, limit_price: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_price = float(limit_price)
        except:
            self.limit_order_callback(
                False, "I don't understand your limit price")
            return True
        try:
            limit_ammount = self.limit_sell_ammount_entry.get()
            limit_ammount = float(limit_ammount)
        except:
            print("limit_ammount is problem")
            return True

        if type(limit_price) is float and type(limit_ammount) is float:
            limit_total = limit_ammount * limit_price
            self.limit_sell_total_string.set(
                Aid.round_to_5_sig_fig(limit_total))
        return True

    def limit_sell_ammount_changed(self, callback_code: str, limit_ammount: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_ammount = float(limit_ammount)
        except:
            self.limit_order_callback(False, "limit_ammount is not a float")
            return True
        try:
            limit_price = self.limit_sell_price_entry.get()
            limit_price = float(limit_price)
        except:
            print("limit_prince is problem")
            return True
        coin = self.current_symbol.removesuffix("USDT")
        coin_balance = self.manager.get_coin_ammount(coin)
        if coin_balance < limit_ammount:
            if limit_price == 0:
                print("limit price")
                return True
            limit_ammount = coin_balance
            self.hack_workaround(
                "limit_sell_ammount", Aid.round_to_5_sig_fig(limit_ammount))
            self.limit_order_callback(
                False, "limit ammount set to max ammount")
        limit_total = limit_ammount*limit_price
        self.limit_sell_total_string.set(Aid.round_to_5_sig_fig(limit_total))
        return True

    def limit_sell_total_changed(self, callback_code: str, limit_total: str) -> bool:
        if callback_code != "1":
            return True
        try:
            limit_total = float(limit_total)
        except:
            self.limit_order_callback(
                False, "I don't understand limit total")
            return True
        try:
            limit_ammount = self.limit_sell_ammount_entry.get()
            limit_ammount = float(limit_ammount)
        except:
            print("limit_ammount is a problem")
            return True
        limit_price = limit_total / limit_ammount
        self.limit_sell_price_string.set(
            Aid.round_to_5_sig_fig(limit_price))
        return True

    def limit_sell_decrement_pressed(self, *args) -> None:
        try:
            current_price = self.limit_sell_price_entry.get()
            current_price = float(current_price)
        except:
            print("can't understand price")
            return
        new_price = current_price * 0.99
        self.limit_sell_price_string.set(Aid.round_to_5_sig_fig(new_price))
        self.limit_sell_price_changed("1", Aid.round_to_5_sig_fig(new_price))

    def limit_sell_zero_pressed(self, *args) -> None:
        try:
            current_price = self.current_price
            current_price = float(current_price)
        except:
            print("can't understand price")
            return
        self.limit_sell_price_string.set(Aid.round_to_5_sig_fig(current_price))
        self.limit_sell_price_changed(
            "1", Aid.round_to_5_sig_fig(current_price))

    def limit_sell_increment_pressed(self, *args) -> None:
        try:
            current_price = self.limit_sell_price_entry.get()
            current_price = float(current_price)
        except:
            print("can't understand price")
            return
        new_price = current_price * 1.01
        self.limit_sell_price_string.set(Aid.round_to_5_sig_fig(new_price))
        self.limit_sell_price_changed("1", Aid.round_to_5_sig_fig(new_price))

    def limit_sell_button_pressed(self, *args) -> None:
        limit_price = float(self.limit_sell_price_string.get())
        limit_ammount = float(self.limit_sell_ammount_string.get())
        self.manager.limit_order(
            False, self.current_symbol, limit_ammount, limit_price, self.limit_order_callback)

    def limit_order_callback(self, executed: bool, reason: str = "") -> None:
        if executed:
            self.report_success(reason)
        else:
            self.report_error(reason)

    def hack_workaround(self, field: str, update_string: str):
        self.hacky_workaround = True
        self.field_to_update = field
        self.update_string = update_string

    # <<< Symbol widgets >>>>

    def symbol_changed(self, event: str) -> None:
        self.current_symbol = event
        self.manager.live_price_subscribe(event, self.update_live_price)
        self.current_price_label.config(text="Connecting")
        coin_name = self.current_symbol.removesuffix('USDT')
        self.market_quantity_label.config(
            text=f"Ammount {coin_name}")
        self.price_label.config(text=f"1{coin_name} =")
        self.symbol_changed_flag = True

    def update_live_price(self, new_price: str) -> None:
        self.current_price = new_price
        if (self.current_price):
            self.current_price_label.config(
                text=Aid.round_to_5_sig_fig(self.current_price))
        if (self.symbol_changed_flag):
            self.symbol_changed_flag = False
            self.limit_buy_price_string.set(Aid.round_to_5_sig_fig(new_price))
            self.limit_sell_price_string.set(
                Aid.round_to_5_sig_fig(new_price))

    async def updater(self, interval: float) -> None:
        while True:
            if self.error_decounter != 0:
                self.error_decounter -= 1
                if self.error_decounter == 0:
                    self.debug_label.config(text="...")

            if self.hacky_workaround:
                self.hacky_workaround = False
                if self.field_to_update == "limit_buy_ammount":
                    self.limit_buy_ammount_string.set(self.update_string)
                elif self.field_to_update == "limit_buy_total":
                    self.limit_buy_total_string.set(self.update_string)
                elif self.field_to_update == "limit_sell_ammount":
                    self.limit_sell_ammount_string.set(self.update_string)
                elif self.field_to_update == "limit_sell_total":
                    self.limit_sell_total_string.set(self.update_string)

            self.update()
            await asyncio.sleep(interval)

    def random_button_pressed(self):
        self.account_info_scrollable.config(state="normal")
        self.account_info_scrollable.delete("1.0", "end")
        self.account_info_scrollable.insert(
            tk.INSERT, chars=self.manager.get_account_info())
        self.account_info_scrollable.config(state="disabled")

    def report_error(self, error: str) -> None:
        self.debug_label.config(text=error)
        self.error_decounter = 120

    def report_success(self, success: str) -> None:
        self.debug_label.config(text=success)
        self.error_decounter = 60

    def close(self) -> None:
        closing_dict = self.manager.on_close_start()
        self.closer(closing_dict)
        self.destroy()
        self.manager.on_close_end()


async def main(loop: asyncio.AbstractEventLoop):
    manager = Manager(loop)
    with open("akaunt.txt", "r+") as f:
        try:
            data = json.load(f)
        except:
            data = {"account_info": {
                "balance":  {"USDT": 1000},
                "starting_balance": 1000
            },
            "old_orders": []
            }

    account_info = data["account_info"]
    manager.create_account(account_info)
    await manager.create_api()
    old_orders = data["old_orders"]
    manager.add_old_orders(old_orders)
    app = TestAPP(manager, closer)
    


def closer(closing_dict: dict) -> None:
    with open("akaunt.txt", "w+") as f:
        json.dump(closing_dict, f, indent=4)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()
    loop.close()
