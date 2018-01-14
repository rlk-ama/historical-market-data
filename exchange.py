
import sys

from enum import Enum
from bittrex import *

class decision(Enum):
    BUY = 1
    SELL = 0
    HOLD = 2

class exchange:
    def __init__(self):
        pass

    def _get_view_exchange(self):
        pass

    def _get_buy_exchange(self):
        pass

    def set_balances(self):
        pass

    def get_orderbook(self, coin):
        pass

    def sell_coin(self, coin, amount=None):
        pass

    def buy_coin(self, coin, amount):
        pass

class TestExchange(exchange):
    def __init__(self):
        Coin('ADA', 10)
        Coin('BCC', 10)
        Coin('BTC', 50)
        Coin('BTG', 10)
        Coin('DASH', 10)
        Coin('ETC', 10)
        Coin('ETH', 10)
        Coin('LTC', 10)
        Coin('NEO', 10)
        Coin('NXT', 10)
        Coin('OMG', 10)
        Coin('XMR', 10)
        Coin('XRP', 10)
        Coin('XVG', 10)
        Coin('ZEC', 10)
        #Always keep some USDT to use to buy with in the next round
        Coin('USDT', 50)
        self.line_number = 2

    def _get_view_exchange(self):
        pass

    def _get_buy_exchange(self):
        pass

    def set_balances(self):
        for coin in Coin.get_all_coins():
            if coin.symbol != 'USDT':
                coin.set_balance(0)
                print "Set balance for {symbol} to 0.".format(symbol=coin.symbol)
            else:
                coin.set_balance(400)
                print "Set balance for USDT to 400."

    def get_orderbook(self, coin):
        file = open("cryptodumps/usdt-{symbol}".format(symbol=coin.symbol.lower()), "r") 
        line = ''
        l = 0
        while l <= self.line_number:
            line = file.readline()
            l += 1
        file.close()
        self.line_number += 1


        amount = float(line.split(',')[1])
        return ({'Rate':amount},{'Rate':amount})

    def buy_coin(self, coin, amount=None):
        #Get current USDT balance
        usdt = Coin.getCoin('USDT')
        #Get amount to buy
        print usdt.get_balance()
        print coin.ratio()
        amount_to_buy_in_usdt = 1.0 * usdt.get_balance() * coin.ratio()

        buy, sell = self.get_orderbook(coin)

        coin.set_balance(1.0 * amount_to_buy_in_usdt / sell.get('Rate'))
        usdt.set_balance(-amount_to_buy_in_usdt, add=True)
        print "Buying ${usdt} of {symbol} for {rate}.".format(usdt=amount_to_buy_in_usdt, symbol=coin.symbol, rate=sell.get('Rate'))
        return True

    def sell_coin(self, coin):
        usdt = Coin.getCoin('USDT')

        buy, sell = self.get_orderbook(coin)
        amount_of_coins = coin.get_balance()

        coin.set_balance(0)
        usdt.set_balance(1.0 * amount_of_coins * buy.get('Rate'), add=True)
        return True

class BittrexExchange(exchange):
    __view_api_key = ""
    __view_api_secret = ""
    __buy_api_key = ""
    __buy_api_secret = ""

    def __init__(self):
        #Retrieve and set api keys
        pass

    def _get_view_exchange(self):
        return Bittrex("view_api_key","view_api_secret")

    def _get_buy_exchange(self):
        return Bittrex("buy_sell_api_key","buy_sell_api_secret")

    def set_balances(self):
        # These things can get stuck, so any api call should be abstracted away and rerun multpile times if it breaks
        view_bit = self._get_view_exchange()
        result = view_bit.get_balances()
        if result.get('success',False) is True:
            for coin in Coin.get_all_coins():
                coin.set_balance(result.get('result',{}).get(coin.symbol, {}).get('Available',0))

    def get_orderbook(self, coin):
        orders = view_bit.get_orderbook(coin.get_exchange_name)
        assert orders.get('success', False) is True
        buy = sorted(orders.get(result, {}).get(buy,[]), key=lambda x: x['Rate'], reverse=True)
        sell = sorted(orders.get(result, {}).get(sell,[]), key=lambda x: x['Rate'])
        return (buy, sell)

    def sell_coin(self, coin, amount=None):
        #Get current USDT balance
        usdt = Coin.getBalanceForCoin('USDT')
        #Get amount to buy
        amount = 1.0 * usdt * coin.ratio()

    def buy_coin(self, coin, amount):
        #set balance as well
        pass


class Coin:
    __quantity = 0
    __instances = []

    def __init__(self, symbol, share):
        self.symbol = symbol
        self.share = share
        self.__balance = 0
        self.exchange_decision = decision.HOLD
        Coin.__quantity += share
        Coin.__instances.append(self)

    def ratio(self):
        return 1.0 * self.share / Coin.__quantity

    def set_balance(self, amount, add=False):
        if add:
            self.__balance += amount
        else:
            self.__balance = amount

    def get_balance(self):
        return self.__balance

    def set_exchange_decision(self, decision):
        self.exchange_decision = decision

    def get_exchange_decision(self):
        return self.exchange_decision

    def get_exchange_name(self):
        return 'USDT_{symbol}'.format(symbol=self.symbol)

    @classmethod
    def get_all_coins(cls):
        return cls.__instances

    @classmethod
    def get_ordered_coins(cls):
        return sorted(cls.__instances, key=lambda x: x.exchange_decision.value)

    @classmethod
    def getCoin(cls, symbol):
        coin = None
        for c in cls.__instances:
            if c.symbol == symbol:
                coin = c
        return c

    @classmethod
    def getBalanceForCoin(cls,symbol):
        return cls.getCoin(symbol).get_balance()

import random
def get_buysell_decisions(sell_all=False):
    for coin in Coin.get_all_coins():
        r = random.uniform(0,1)
        if sell_all == True:
            dec = decision.SELL
        elif r > 0.9:
            dec = decision.SELL
        elif r > 0.8:
            dec = decision.BUY
        else:
            dec = decision.HOLD
        coin.set_exchange_decision(dec)

def do_buy_and_sell(exchange):
    # First sell coins to sell, then buy coins to buy.
    for coin in Coin.get_ordered_coins():
        if coin.get_exchange_decision() == decision.HOLD or coin.symbol == 'USDT':
            continue
        if coin.get_exchange_decision() == decision.SELL:
            exchange.sell_coin(coin)
        if coin.get_exchange_decision() == decision.BUY:
            exchange.buy_coin(coin)


if __name__ == "__main__":
    exchange = TestExchange()

    exchange.set_balances()

    for i in range(10):

        get_buysell_decisions()

        do_buy_and_sell(exchange)

    get_buysell_decisions(sell_all = True)
    do_buy_and_sell(exchange)
    print "Final USDT balance = {balance}".format(balance=Coin.getCoin('USDT').get_balance())
