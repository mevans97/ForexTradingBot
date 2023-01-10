import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time

#------------------------------------------------------------------------
#functions so we wont have to keep re-typing code 
#------------------------------------------------------------------------

# 1.) function to send a market order

def market_order(symbol, volume, order_type, **kwargs):
    tick = mt5.symbol_info_tick(symbol)

    order_dict = {'buy': 0, 'sell': 1}
    price_dict = {'buy': tick.ask, 'sell': tick.bid}

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol, #The name of the trading instrument, for which the order is placed
        "volume": volume, #Requested volume of a deal in lots. A real volume when making a deal depends on an order execution type.
        "type": order_dict[order_type], #Order type. The value can be one of the values of the ORDER_TYPE enumeration
        "price": price_dict[order_type], #Price at which an order should be executed. The price is not set in case of market orders for instruments of the "Market Execution"
        "deviation": DEVIATION, #Maximum acceptable deviation from the requested price 
        "magic": 100, #EA ID. Allows arranging the analytical handling of trading orders. Each EA can set a unique ID when sending a trading request
        "comment": "python market order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    print(order_result)

    return order_result

#------------------------------------------------------------------------

# 2.)function to close an order base don ticket id

def close_order(ticket):
    positions = mt5.positions_get()

    for pos in positions: #Looks through all open positions to find ticket matching order
        tick = mt5.symbol_info_tick(pos.symbol)
        type_dict = {0: 1, 1: 0}  # 0 represents buy, 1 represents sell - inverting order_type to close the position
        price_dict = {0: tick.ask, 1: tick.bid}

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": type_dict[pos.type],
                "price": price_dict[pos.type],
                "deviation": DEVIATION,
                "magic": 100,
                "comment": "python close order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            order_result = mt5.order_send(request)
            print(order_result)

            return order_result

    return 'Ticket does not exist'

#----------------------------------------------------------------------------------

# 3.) function to get the exposure of a symbol
# Exposure shows how many open positions you have of a certain symbol. Pandas is used to go through volume column and get sum of exposure

def get_exposure(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        exposure = pos_df['volume'].sum()

        return exposure

#-----------------------------------------------------------------------------------

# 4.) function to look for trading signals
# 

def signal(symbol, timeframe, sma_period):
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 1, sma_period) #Gets us candlestick bar information
    bars_df = pd.DataFrame(bars) #passes candlestick information to pandas for display purposes

    last_close = bars_df.iloc[-1].close # gets candlestick closing value using last row in pandas data frame
    sma = bars_df.close.mean() # This gets us the simple moving average indicator.
    '''
    A simple moving average (SMA) is an arithmetic moving average calculated by adding recent prices and then dividing 
    that figure by the number of time periods in the calculation average.

    '''

    #Here is the actual signal
    direction = 'flat' #This makes it so no action is taken
    if last_close > sma:
        direction = 'buy' #This sends a buy signal
    elif last_close < sma:
        direction = 'sell' #This sends a sell signal

    return last_close, sma, direction

#-----------------------------------------------------------------------------------------

# MAIN METHODS

if __name__ == '__main__' :

    # display data on the MetaTrader 5 package. This shows the author and version of the package used
    print("MetaTrader5 package author: ",mt5.__author__)
    print("MetaTrader5 package version: ",mt5.__version__)


    # establish connection to the MetaTrader 5 terminal. we can just use mt5.initialize() however we want to push an error if it is not initialized
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()

    account= 65385484 # my account number for my demo account
    password="wm6jjnof" # my account password for my demo account
    server = "MetaQuotes-Demo"

    authorized=mt5.login(account, password, server) #login function with account and password as parameters
    # message runs if the login fails

    if not authorized:
        print("failed to connect at account #{}, error code: {}".format(account, mt5.last_error()))

    #info is displayed if the login works    

    else:
        print("Account Connected !\n")

        # turn trading account data into the form of a dictionary
        account_info_dict = mt5.account_info()._asdict()
        
        # convert the dictionary into DataFrame and print using pandas API
        df=pd.DataFrame(list(account_info_dict.items()),columns=['property','value'])
        print("account_info() as dataframe:")
        print(df)
    
    
    # strategy parameters
    # This is for a simple moving average strategy.
    SYMBOL = "EURUSD"
    VOLUME = 1.0
    TIMEFRAME = mt5.TIMEFRAME_M1
    SMA_PERIOD = 10
    DEVIATION = 20

    #-----------------------------------------------------------------------------------------------
    #Loop For The Trade Signals

    while True:
        # calculating account exposure
        exposure = get_exposure(SYMBOL)

        # calculating last candle close and simple moving average and checking for trading signal
        last_close, sma, direction = signal(SYMBOL, TIMEFRAME, SMA_PERIOD)

        # trading logic
        if direction == 'buy':
            # if we have a BUY signal, close all short positions
            for pos in mt5.positions_get():
                if pos.type == 1:  # pos.type == 1 represent a sell order
                    close_order(pos.ticket)

            # if there are no open positions, open a new long position
            if not mt5.positions_total():
                market_order(SYMBOL, VOLUME, direction)

        elif direction == 'sell':
            # if we have a SELL signal, close all short positions
            for pos in mt5.positions_get():
                if pos.type == 0:  # pos.type == 0 represent a buy order
                    close_order(pos.ticket)

            # if there are no open positions, open a new short position
            if not mt5.positions_total():
                market_order(SYMBOL, VOLUME, direction)

        print('time: ', datetime.now())
        print('exposure: ', exposure)
        print('last_close: ', last_close)
        print('sma: ', sma)
        print('signal: ', direction)
        print('-------\n')

        # update every 1 second
        time.sleep(1)
