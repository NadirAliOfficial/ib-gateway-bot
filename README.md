
# IB Gateway Python Integration

A minimal Python script that connects to Interactive Brokers Gateway (or TWS) via `ibapi`, fetches your live account summary and real-time PnL, and logs everything to the console.

## 🚀 Features

- **Account Summary**: Net liquidation, cash balances, margin requirements, available funds  
- **Real-Time PnL**: Daily, unrealized, and realized profit & loss updates  
- **Detailed Logging**: Records all API requests, responses, and errors  

## 🛠 Prerequisites

- **Python 3.10+**  
- **IB Gateway or TWS** running with API access enabled (default port `7497`)  

Install the IB API client:

```bash
pip install ibapi
````

## ▶️ Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/NadirAliOffical/ib-gateway-bot.git
   cd ib-gateway-bot
   ```

2. **Configure**
   Open `bot.py` and update the `host`, `port`, and `clientId` values if necessary.

3. **Run**

   ```bash
   python bot.py
   ```



