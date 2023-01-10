# ForexTradingBot
Forex bot that uses MetaTrader's Python Integration API

The Documentation For The MetaTrader API : https://www.mql5.com/en/docs/integration/python_metatrader5

Documentation For The Pandas API : https://pandas.pydata.org/docs/index.html#

I used a simple moving average indicator to make the bot.

V1: Bot executes trades every second. When candlestick closes above sma line, the bot executes a buy. When candlestick closes below sma line, the bot executes a sell.
