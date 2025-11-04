from flask import Flask, request, jsonify, render_template
import yfinance as yf
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stock', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    if not symbol:
        return jsonify({"error": "Please provide a stock symbol, e.g. /stock?symbol=AAPL"}), 400

    try:
        # --- Fetch data directly from yfinance ---
        stock = yf.Ticker(symbol)
        hist = stock.history(period="7d")

        # Fetch general info
        info = stock.info

        # Prepare historical price list
        history = [
            {"date": str(date.date()), "close": round(row["Close"], 2)}
            for date, row in hist.iterrows()
        ]

        # Extract values safely
        price = info.get("currentPrice", None)
        change = info.get("regularMarketChange", None)
        percent = info.get("regularMarketChangePercent", None)
        market_cap = info.get("marketCap", None)

        # If missing (some tickers), fallback to last known values
        if not price and not hist.empty:
            price = round(hist["Close"].iloc[-1], 2)
        if change is None:
            change = 0
        if percent is None:
            percent = 0

        return jsonify({
            "symbol": symbol,
            "name": info.get("longName", "Unknown"),
            "price": round(price, 2) if price else 0,
            "change": round(change, 2),
            "percent_change": f"{round(percent, 2)}%",
            "market_cap": market_cap if market_cap else 0,
            "exchange": info.get("exchange", "N/A"),
            "history": history
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
