import ccxt
from datetime import datetime
from flask import render_template, Blueprint
from flask_login import login_required

KRAKEN_BUY_FEE, KRAKEN_SELL_FEE = 0.0016, 0.0026
BITSMAP_BUY_FEE, BITSMAP_SELL_FEE = 0.003, 0.004
FLAT_FEE = 0.001  # BINANCE, 0.5 GATE, KUCOIN



class Counter:
    self = 0
    arbitrage_number = 0

    def add(self, value):
        Counter.self += value
        Counter.arbitrage_number += 1
        print('counter is ', round(Counter.self, 4))


class ArbitrageFormat:
    def __init__(self, i_symbol, i_ask_price, i_exchange1, i_bid_price, i_exchange2, i_opportunity):
        self.number = Counter.arbitrage_number
        self.date_time = datetime.now()
        self.symbol = i_symbol
        self.ask_price = i_ask_price
        self.bid_price = i_bid_price
        self.profit = round(i_opportunity, 4)
        self.exchange1 = i_exchange1
        self.exchange2 = i_exchange2
        self.counter = Counter.self


# to store count of objects created
def arbitrage(exchange1, exchange2, symbol, Counter, arbitrage_output):
    # Get the order book for the two exchanges
    if ((exchange1 == gate or exchange1 == kraken or exchange1 == bitstamp) and
            (exchange2 == kraken or exchange2 == bitstamp)):
        new_symbol = str(symbol[:-1])
        order_book1 = exchange1.fetch_ticker(new_symbol)
        order_book2 = exchange2.fetch_ticker(new_symbol)
    elif (exchange1 == gate) or (exchange1 == kraken) or (exchange1 == bitstamp):
        new_symbol = str(symbol[:-1])
        order_book1 = exchange1.fetch_ticker(new_symbol)
        order_book2 = exchange2.fetch_ticker(symbol)
    elif (exchange2 == gate) or (exchange2 == kraken) or (exchange2 == bitstamp):
        new_symbol = str(symbol[:-1])
        order_book1 = exchange1.fetch_ticker(symbol)
        order_book2 = exchange2.fetch_ticker(new_symbol)
    else:
        order_book1 = exchange1.fetch_ticker(symbol)
        order_book2 = exchange2.fetch_ticker(symbol)

    # Get the best ask and bid prices
    ask_price1 = order_book1['ask']
    bid_price2 = order_book2['bid']
    ask_price1, bid_price2 = calculate_buying_precent(ask_price1, bid_price2, exchange1, my_wallet)
    ask_price2 = order_book2['ask']
    bid_price1 = order_book1['bid']
    ask_price2, bid_price1 = calculate_buying_precent(ask_price2, bid_price1, exchange2, my_wallet)
    # Calculate the arbitrage opportunity
    # bid_price = highest buying price, ask_price = lowest selling price

    opportunity1 = bid_price2 - ask_price1  # calculate_with_fee(bid_price2, ask_price1, exchange2, exchange1)
    opportunity2 = bid_price1 - ask_price2  # calculate_with_fee(bid_price1, ask_price2, exchange1, exchange2)
    if opportunity1 > 0:
        # Calculate the amount of cryptocurrency to buy and sell
        if (my_wallet[str(exchange2)]["USDT"] < ask_price1):
            transform_money(exchange2, exchange1, ask_price1, my_wallet)

        amount = min(ask_price1, bid_price2)
        Counter.add(Counter.self, opportunity1)
        arbitrage_output.append(ArbitrageFormat(symbol, ask_price1, exchange2, bid_price2, exchange1, opportunity1))
        print(
            'Opportunity found: Buy {} for {}$ in {} and sell it on {} in {} '
            ',neto profit is {}$ (include fees)'.format(symbol, ask_price1, exchange2, bid_price2, exchange1,
                                                       round(opportunity1, 4)))

        my_wallet[str(exchange1)]["USDT"] += bid_price2
        my_wallet[str(exchange2)]["USDT"] -= ask_price1
        print(my_wallet)  # debug print
        total = 0
        for market in my_wallet:
            total += my_wallet[str(market)]["USDT"]
        print(total)
        # exchange1.create_order(symbol, 'limit', 'buy', amount, ask_price1)
        # exchange2.create_order(symbol, 'limit', 'sell', amount, bid_price2)
    if opportunity2 > 0:
        if (my_wallet[str(exchange1)]["USDT"] < ask_price2):
            transform_money(exchange1, exchange2, ask_price2, my_wallet)
        # Calculate the amount of cryptocurrency to buy and sell
        amount = min(bid_price1, ask_price2)

        Counter.add(Counter.self, opportunity2)
        arbitrage_output.append(ArbitrageFormat(symbol, ask_price2, exchange1, bid_price1, exchange2, opportunity2))

        print(
           'Opportunity found: Buy {} for {}$ in {} and sell it on {} in {} '
           ',neto profit is {}$ (include fees)'.format(symbol, ask_price2, exchange1, bid_price1, exchange2,
                                                       round(opportunity2, 4)))
        my_wallet[str(exchange2)]["USDT"] += bid_price1
        my_wallet[str(exchange1)]["USDT"] -= ask_price2
        print(my_wallet)  # debug print
        total = 0
        for market in my_wallet:
            total += my_wallet[str(market)]["USDT"]
        print(total)

        # Place the buy and sell orders
        # exchange1.create_order(symbol, 'limit', 'buy', amount, ask_price1)
        # exchange2.create_order(symbol, 'limit', 'sell', amount, bid_price2)


def transform_money(buy_market, sell_market, ask_price1, my_wallet):
    out = False
    if my_wallet[str(sell_market)]["USDT"] >= ask_price1:
        my_wallet[str(buy_market)]["USDT"] += ask_price1
        my_wallet[str(sell_market)]["USDT"] -= ask_price1
    else:
        for market in my_wallet:
            if my_wallet[str(market)]["USDT"] >= ask_price1 and market != buy_market:
                my_wallet[str(buy_market)]["USDT"] += my_wallet[str(market)]["USDT"]
                my_wallet[str(market)]["USDT"] -= ask_price1
                out = True
                break
        if (out == False):
            for market in my_wallet:
                if my_wallet[str(market)]["USDT"] > 0 and my_wallet[str(buy_market)]["USDT"] < ask_price1 \
                        and market != buy_market:
                    my_wallet[str(buy_market)]["USDT"] += my_wallet[str(market)]["USDT"]
                    my_wallet[str(market)]["USDT"] = 0


# bid_price = highest buying price, ask_price = lowest selling price
def calculate_with_fee(sell_price, buy_price, buy_platform, sell_platform):
    bruto_profit, tmp_profit, buy_fees = sell_price - buy_price, 0.0, 0.0  # profit > 0
    if bruto_profit <= 0:
        return 0

    # calculate buy fees
    if buy_platform == binance or buy_platform == kucoin:
        buy_fees = buy_price * FLAT_FEE
    elif buy_platform == kraken:
        buy_fees = buy_price * KRAKEN_BUY_FEE
    elif buy_platform == bitstamp:
        buy_fees = buy_price * BITSMAP_BUY_FEE
    elif buy_platform == gate:
        buy_fees = buy_price * FLAT_FEE * 2
    else:
        return 0

    # calculate sell fees = (profit after sell fees) - (buy fees)
    if sell_platform == sell_platform == binance or sell_platform == kucoin:
        return (bruto_profit * (1 - FLAT_FEE)) - buy_fees
    elif sell_platform == kraken:
        return (bruto_profit * (1 - KRAKEN_SELL_FEE)) - buy_fees
    elif sell_platform == bitstamp:
        return (bruto_profit * (1 - BITSMAP_SELL_FEE)) - buy_fees
    elif buy_platform == gate:
        return (bruto_profit * (1 - 2 * FLAT_FEE)) - buy_fees
    return 0


# ask = קנייה
# bid = מכירה
def calculate_buying_precent(ask_price, bid_price, ask_market, my_wallet):
    part_of_coin = my_wallet[str(ask_market)]["USDT"] / ask_price
    bid_price = bid_price * part_of_coin
    ask_price = ask_price * part_of_coin
    return ask_price, bid_price


# Create the exchanges
binance = ccxt.binance()
gate = ccxt.gate()
kraken = ccxt.kraken()
kucoin = ccxt.kucoin()
bitstamp = ccxt.bitstamp()
binance.load_markets()
gate.load_markets()
kraken.load_markets()
kucoin.load_markets()
bitstamp.load_markets()

markets = [binance, gate, kraken, kucoin, bitstamp]
binance_wallet = {"BTC": 0.1, "ETH": 0.5, "LTC": 1.0, "USDT": 10000.0}
gate_wallet = {"BTC": 0.1, "ETH": 0.5, "LTC": 1.0, "USDT": 10000.0}
kraken_wallet = {"BTC": 0.1, "ETH": 0.5, "LTC": 1.0, "USDT": 10000.0}
kucoin_wallet = {"BTC": 0.1, "ETH": 0.5, "LTC": 1.0, "USDT": 10000.0}
bitstamp_wallet = {"BTC": 0.1, "ETH": 0.1, "LTC": 1.0, "USDT": 10000.0}
my_wallet = {"Binance": binance_wallet, "Gate.io": gate_wallet, "Kraken": kraken_wallet, "KuCoin": kucoin_wallet, "Bitstamp": bitstamp_wallet}
symbol = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT']


arbitrage_blue_print = Blueprint('arbitrage', __name__)


# Run the arbitrage algorithm every minute
@arbitrage_blue_print.route('/arbitrage', methods=['GET', 'POST'])
@login_required
def run_arbitrage():
    global symbol
    arbitrage_output = []
    while True:
        for exchange1 in markets:
            for exchange2 in markets:
                if exchange1 != exchange2:
                    for coin in symbol:
                        arbitrage(exchange1, exchange2, coin, Counter, arbitrage_output)
        # time.sleep(60)
        return render_template('arbitrage.html', output=arbitrage_output)


