# Forex candles and technical analysis

TradeAI's Forex Technical Analysis section requests real OHLC bars from Twelve Data through the server-side endpoint `/api/candles`.

## Setup

1. Create a Twelve Data account at https://twelvedata.com/ and obtain an API key.
2. In Vercel, open TradeAI → Settings → Environment Variables.
3. Add `TWELVE_DATA_API_KEY` with the provider key, for Production (and Preview if needed).
4. Redeploy the project after adding the variable.

Never place the key in frontend JavaScript or commit it to GitHub. Provider plans, rate limits, instrument coverage, and whether quotes are real-time or delayed depend on the account and data plan.

## Included analysis

- OHLC candlesticks, OHLC bars, or close-price wave view
- Configurable major FX pairs and timeframes
- SMA 20 and SMA 50
- RSI (14)
- MACD (12/26 EMA difference)
- Bollinger Band range (20 periods, 2 standard deviations)
- ATR (14) as a volatility estimate
- Transparent heuristic bias score based on trend, RSI, and MACD

The bias is a simple technical heuristic and is not a calibrated prediction model. It does not guarantee direction or profit. Volume is not shown as FX spot markets generally do not provide a consolidated exchange-traded volume series; the provider's optional volume field may be zero or unavailable.
