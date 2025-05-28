
import logging
from collections import deque
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

class IBApp(EWrapper, EClient):
    TICKERS     = ["AAPL", "MSFT", "GOOG"]  # add as many symbols as you like
    FAST_EMA    = 9
    SLOW_EMA    = 20
    RSI_PERIOD  = 14
    BAR_SECONDS = 60
    QTY         = 100

    def __init__(self):
        EClient.__init__(self, wrapper=self)
        self.nextOrderId    = None
        # state per reqId: closes, ema_fast, ema_slow, prev_diff, ordered, symbol, contract
        self.symbol_states  = {}

    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        logging.info(f"▶ Connected (nextOrderId={orderId})")
        # subscribe each ticker on its own reqId
        for i, symbol in enumerate(self.TICKERS, start=1):
            state = {
                "closes": deque(maxlen=self.SLOW_EMA+1),
                "ema_fast": None,
                "ema_slow": None,
                "prev_diff": None,
                "ordered": False,
            }
            # build contract
            c = Contract()
            c.symbol   = symbol
            c.secType  = "STK"
            c.exchange = "SMART"
            c.currency = "USD"
            state["contract"] = c
            self.symbol_states[i] = state
            # subscribe
            self.reqRealTimeBars(i, c, self.BAR_SECONDS, "TRADES", False, [])
            logging.info(f"▶ Subscribed to real‐time bars for {symbol} (reqId={i})")

    def realTimeBar(self, reqId, time, open_, high, low, close, volume, wap, count):
        state = self.symbol_states.get(reqId)
        if not state or state["ordered"]:
            return

        closes = state["closes"]
        closes.append(close)
        if len(closes) < self.SLOW_EMA:
            return

        # initialize or update EMAs
        if state["ema_fast"] is None:
            state["ema_fast"] = sum(list(closes)[-self.FAST_EMA:]) / self.FAST_EMA
            state["ema_slow"] = sum(list(closes)[-self.SLOW_EMA:]) / self.SLOW_EMA
        else:
            kf = 2 / (self.FAST_EMA + 1)
            ks = 2 / (self.SLOW_EMA + 1)
            state["ema_fast"] = close * kf + state["ema_fast"] * (1 - kf)
            state["ema_slow"] = close * ks + state["ema_slow"] * (1 - ks)

        diff = state["ema_fast"] - state["ema_slow"]

        # compute RSI
        gains, losses = [], []
        lst = list(closes)
        for i in range(1, self.RSI_PERIOD+1):
            d = lst[-i] - lst[-i-1]
            if d > 0: gains.append(d)
            else:      losses.append(-d)
        avg_gain = sum(gains) / self.RSI_PERIOD
        avg_loss = sum(losses) / self.RSI_PERIOD
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain/avg_loss))

        symbol = state["contract"].symbol
        logging.info(f"{symbol} | close={close:.2f} | EMA_diff={diff:.4f} | RSI={rsi:.2f}")

        # signal on crossover
        if state["prev_diff"] is not None:
            if diff > 0 and state["prev_diff"] <= 0 and rsi > 50:
                self.place_market_order(symbol, "BUY")
                state["ordered"] = True
            elif diff < 0 and state["prev_diff"] >= 0 and rsi < 50:
                self.place_market_order(symbol, "SELL")
                state["ordered"] = True

        state["prev_diff"] = diff

    def place_market_order(self, symbol, action):
        oid = self.nextOrderId
        # find the contract for this order
        contract = next(s["contract"] for s in self.symbol_states.values()
                        if s["contract"].symbol == symbol)
        order = Order()
        order.orderId       = oid
        order.action        = action
        order.orderType     = "MKT"
        order.totalQuantity = self.QTY
        order.transmit      = True
        logging.info(f"▶ Placing {action} #{oid} x{self.QTY} for {symbol}")
        self.placeOrder(oid, contract, order)
        self.nextOrderId += 1

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        logging.info(f"OrderStatus | id={orderId} | status={status} | filled={filled} @ {avgFillPrice}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    app = IBApp()
    app.connect("127.0.0.1", 7497, clientId=1)
    logging.info("▶ Connecting to IB Gateway...")
    app.run()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
bot_multi.py

Milestone 3 Extension – Multi‐Ticker EMA/RSI Market‐Order Executor.
  • Subscribes to real‐time bars for multiple symbols
  • Computes EMA(9)/EMA(20) cross + RSI(14) per symbol
  • Places one market order per symbol when its signal fires
"""

import logging
from collections import deque
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

class IBApp(EWrapper, EClient):
    TICKERS     = ["AAPL", "MSFT", "GOOG"]  # add as many symbols as you like
    FAST_EMA    = 9
    SLOW_EMA    = 20
    RSI_PERIOD  = 14
    BAR_SECONDS = 60
    QTY         = 100

    def __init__(self):
        EClient.__init__(self, wrapper=self)
        self.nextOrderId    = None
        # state per reqId: closes, ema_fast, ema_slow, prev_diff, ordered, symbol, contract
        self.symbol_states  = {}

    def nextValidId(self, orderId):
        self.nextOrderId = orderId
        logging.info(f"▶ Connected (nextOrderId={orderId})")
        # subscribe each ticker on its own reqId
        for i, symbol in enumerate(self.TICKERS, start=1):
            state = {
                "closes": deque(maxlen=self.SLOW_EMA+1),
                "ema_fast": None,
                "ema_slow": None,
                "prev_diff": None,
                "ordered": False,
            }
            # build contract
            c = Contract()
            c.symbol   = symbol
            c.secType  = "STK"
            c.exchange = "SMART"
            c.currency = "USD"
            state["contract"] = c
            self.symbol_states[i] = state
            # subscribe
            self.reqRealTimeBars(i, c, self.BAR_SECONDS, "TRADES", False, [])
            logging.info(f"▶ Subscribed to real‐time bars for {symbol} (reqId={i})")

    def realTimeBar(self, reqId, time, open_, high, low, close, volume, wap, count):
        state = self.symbol_states.get(reqId)
        if not state or state["ordered"]:
            return

        closes = state["closes"]
        closes.append(close)
        if len(closes) < self.SLOW_EMA:
            return

        # initialize or update EMAs
        if state["ema_fast"] is None:
            state["ema_fast"] = sum(list(closes)[-self.FAST_EMA:]) / self.FAST_EMA
            state["ema_slow"] = sum(list(closes)[-self.SLOW_EMA:]) / self.SLOW_EMA
        else:
            kf = 2 / (self.FAST_EMA + 1)
            ks = 2 / (self.SLOW_EMA + 1)
            state["ema_fast"] = close * kf + state["ema_fast"] * (1 - kf)
            state["ema_slow"] = close * ks + state["ema_slow"] * (1 - ks)

        diff = state["ema_fast"] - state["ema_slow"]

        # compute RSI
        gains, losses = [], []
        lst = list(closes)
        for i in range(1, self.RSI_PERIOD+1):
            d = lst[-i] - lst[-i-1]
            if d > 0: gains.append(d)
            else:      losses.append(-d)
        avg_gain = sum(gains) / self.RSI_PERIOD
        avg_loss = sum(losses) / self.RSI_PERIOD
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain/avg_loss))

        symbol = state["contract"].symbol
        logging.info(f"{symbol} | close={close:.2f} | EMA_diff={diff:.4f} | RSI={rsi:.2f}")

        # signal on crossover
        if state["prev_diff"] is not None:
            if diff > 0 and state["prev_diff"] <= 0 and rsi > 50:
                self.place_market_order(symbol, "BUY")
                state["ordered"] = True
            elif diff < 0 and state["prev_diff"] >= 0 and rsi < 50:
                self.place_market_order(symbol, "SELL")
                state["ordered"] = True

        state["prev_diff"] = diff

    def place_market_order(self, symbol, action):
        oid = self.nextOrderId
        # find the contract for this order
        contract = next(s["contract"] for s in self.symbol_states.values()
                        if s["contract"].symbol == symbol)
        order = Order()
        order.orderId       = oid
        order.action        = action
        order.orderType     = "MKT"
        order.totalQuantity = self.QTY
        order.transmit      = True
        logging.info(f"▶ Placing {action} #{oid} x{self.QTY} for {symbol}")
        self.placeOrder(oid, contract, order)
        self.nextOrderId += 1

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        logging.info(f"OrderStatus | id={orderId} | status={status} | filled={filled} @ {avgFillPrice}")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    app = IBApp()
    app.connect("127.0.0.1", 7497, clientId=1)
    logging.info("▶ Connecting to IB Gateway...")
    app.run()

if __name__ == "__main__":
    main()
