

import logging
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.contract import Contract

class IBApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, wrapper=self)
        self.summary_req_id = 9001
        self.pnl_req_id     = 9002

    def error(self, reqId, errorCode, errorString):
        logging.error(f"Error. ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}")

    def nextValidId(self, orderId):
        logging.info("▶ Connected to IB Gateway.")
        # 1) Account summary
        tags = ",".join([
            AccountSummaryTags.NetLiquidation,
            AccountSummaryTags.TotalCashValue,
            AccountSummaryTags.MaintMarginReq,
            AccountSummaryTags.AvailableFunds,
        ])
        self.reqAccountSummary(self.summary_req_id, "All", tags)
        logging.info(f"▶ Requested account summary (ReqId={self.summary_req_id}).")  # :contentReference[oaicite:0]{index=0}

        # 2) PnL subscription
        # Use empty modelCode ("") for default PnL
        self.reqPnL(self.pnl_req_id, "", "")
        logging.info(f"▶ Subscribed to PnL updates (ReqId={self.pnl_req_id}).")  # :contentReference[oaicite:1]{index=1}

    # Account summary callbacks
    def accountSummary(self, reqId, account, tag, value, currency):
        logging.info(f"✔ [{account}] {tag}: {value} {currency}")

    def accountSummaryEnd(self, reqId):
        logging.info("▶ Account summary complete.")
        self.cancelAccountSummary(reqId)

    # PnL callbacks
    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        logging.info(f"✔ PnL Update. Daily: {dailyPnL}, Unrealized: {unrealizedPnL}, Realized: {realizedPnL}")
        # If you only need one snapshot, you can cancel here:
        # self.cancelPnL(reqId)

    def pnlSingle(self, reqId, pos, dailyPnL, unrealizedPnL, realizedPnL, value):
        # Per-position PnL (optional)
        logging.info(f"✔ PnL Single. Pos: {pos}, Daily: {dailyPnL}, Unrealized: {unrealizedPnL}, Realized: {realizedPnL}")

    def accountDownloadEnd(self, accountName):
        # called when streaming account updates finish
        pass

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = IBApp()
    try:
        app.connect("127.0.0.1", 7497, clientId=1)
        logging.info("▶ Connecting to IB Gateway at 127.0.0.1:7497 (clientId=1)...")
        app.run()
    except Exception as e:
        logging.exception(f"Fatal exception: {e}")
    finally:
        if app.isConnected():
            app.disconnect()
            logging.info("▶ Disconnected cleanly.")

if __name__ == "__main__":
    main()
