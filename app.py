from flask import Flask, request, jsonify, render_template
import requests
import yfinance as yf
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = "azPCN7U59YsRaxvcOiUl3BB2qSnz5ArBmAwEufPe"

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/stock', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    if not symbol:
        return jsonify({"error": "Please provide a stock symbol, e.g. /stock?symbol=AAPL"}), 400

    try:
        # --- Realtime data from StockData.org ---
        quote_url = f"https://api.stockdata.org/v1/data/quote?symbols={symbol}&api_token={API_KEY}"
        quote_data = requests.get(quote_url).json()

        # --- Historical data from yfinance ---
        stock = yf.Ticker(symbol)
        hist = stock.history(period="7d")

        if "data" not in quote_data or len(quote_data["data"]) == 0:
            # If StockData.org fails, fallback completely to yfinance
            info = stock.info
            history = [
                {"date": str(date.date()), "close": round(row["Close"], 2)}
                for date, row in hist.iterrows()
            ]
            return jsonify({
                "symbol": symbol,
                "name": info.get("longName", "Unknown"),
                "price": round(info.get("currentPrice", 0), 2),
                "change": round(info.get("regularMarketChange", 0), 2),
                "percent_change": f"{round(info.get('regularMarketChangePercent', 0), 2)}%",
                "market_cap": info.get("marketCap", 0),
                "exchange": info.get("exchange", "N/A"),
                "history": history
            })

        stock_info = quote_data["data"][0]

        # --- Format Change & Market Cap properly ---
        change_val = stock_info.get("day_change")
        percent_val = stock_info.get("day_change_percent")
        mcap_val = stock_info.get("market_cap")

        # Fallback if None
        if change_val is None or percent_val is None:
            yf_info = stock.info
            change_val = yf_info.get("regularMarketChange")
            percent_val = yf_info.get("regularMarketChangePercent")

        if mcap_val is None:
            yf_info = stock.info
            mcap_val = yf_info.get("marketCap")

        # --- Historical Data ---
        history = []
        if not hist.empty:
            for date, row in hist.iterrows():
                history.append({
                    "date": str(date.date()),
                    "close": round(row["Close"], 2)
                })

        return jsonify({
            "symbol": stock_info.get("ticker"),
            "name": stock_info.get("name"),
            "price": round(stock_info.get("price", 0), 2),
            "change": round(change_val if change_val else 0, 2),
            "percent_change": f"{round(percent_val if percent_val else 0, 2)}%",
            "market_cap": mcap_val if mcap_val else 0,
            "exchange": stock_info.get("exchange_short"),
            "history": history
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
