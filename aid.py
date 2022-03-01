class Aid:
    @staticmethod
    def round_to_5_sig_fig(value) -> str:
        try:
            number = float(value)
        except:
            print("can't turn value to float for rounding to 5 sig figs")
            return ""

        modable_number = number
        decimals = 0
        while not modable_number // 1000 > 0 and decimals < 6:
            modable_number *= 10
            decimals += 1
        return str(round(number, 2+decimals))