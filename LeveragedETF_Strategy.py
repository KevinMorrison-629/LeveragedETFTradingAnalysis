import datetime as dt
import numpy as np
from pandas_datareader import data
import pandas_datareader.data as web
#import plotly.graph_objects as go
import matplotlib.pyplot as plt
#import requests_html
#from yahoo_fin import stock_info as si

import random

#______________________________________________________________________________#

"""The Following simulation is used to determine whether or not it is
a viable trading stratgy to invest in Leveraged index funds through an strategy
I will call Risk Leverage Averaging.

Through this stratgey, the initial principle investment is used to buy a highly
leveraged stock index which has a positive upward trend greater than that of a
traditional broad index fund such as VOO, an index that tracks the S&P 500.

The investment is kept until a certain percentage increase is obtained, at which
point, part of the investment is transferred to an un-Leveraged index fund- such
as the aforementioned S&P 500 index fund VOO.

At this point, part of the initial principal will continue to gain value through
the leverage fund, while the other percentage will gain value through an
UnLeveraged fund.

Should the Leveraged fund increase to a value greater than the initial
principal, the process of taking a percentage of this value and placing it in an
UnLeveraged fund will again be done, continuing until one of the following
occurs: the stock market begins to crash (for example losing more than 10% from all time high)
or at which point the index fund does not return greater than a multiple of the 
index that is Leveraged (typically 3x the UnLeveraged index)"""

#The Following simulation uses the following assumptions

num_sims = 1 #For the initial code, I am just coding it for one simulation

sim_start = dt.datetime(2011,6,5)
sim_end = dt.datetime(2020,6,30)

ticker_1 = 'TQQQ'
ticker_2 = 'VOOG'

stock_data = {}
stock_data['TQQQ'] = web.DataReader('TQQQ','yahoo',sim_start,sim_end)
    #The following removes keys from the dictionary (not really needed for this simulation)
stock_data['TQQQ'].pop('High')
stock_data['TQQQ'].pop('Low')
stock_data['TQQQ'].pop('Open')
stock_data['TQQQ'].pop('Close')

stock_data['VOOG'] = web.DataReader('VOOG','yahoo',sim_start,sim_end)
    #The following removes keys from the dictionary (not really needed for this simulation)
stock_data['VOOG'].pop('High')
stock_data['VOOG'].pop('Low')
stock_data['VOOG'].pop('Open')
stock_data['VOOG'].pop('Close')

des_percent_increase = 0.30
max_time_Leveraged = 160 #in trading days
market_crash_percent = 10 # percent decrease in a week that will correspond to the market having "crashed"

money = 500
total_money_added = money
portfolio = {'Leveraged':{'Shares':0, 'Cost Basis':None}, 'UnLeveraged':{'Shares':0, 'Cost Basis':None}, 'RealEstate':0}
transaction_log = {}

transaction_number = 0
count = 0
prop_number = 0

current_day = 0

leveraged_portfolio_value = np.zeros(2278)
unleveraged_portfolio_value = np.zeros(2278)
money_value = np.zeros(2278)
sim_days = np.zeros(2278)
total_value = np.zeros(2278)


def get_price(day, ticker):
    return stock_data[ticker]['Adj Close'][day]

def buy(type, allocated_money,day):
    '''This function buys a number of shares, num_shares, given a certain amount
    of allocated money for the specified type of purchase (Leveraged or UnLeveraged)'''
    global money
    if allocated_money > money:
        print('Not Enough Money')
        return
    else:
        if type == 'Leveraged':
            price = get_price(day, 'TQQQ')
            num_shares = allocated_money / price
            if not num_shares < 0.05:
                if portfolio[type]['Cost Basis'] == None:
                    portfolio[type]['Cost Basis'] = get_price(day, 'TQQQ')
                portfolio[type]['Cost Basis'] = (allocated_money + (portfolio[type]['Cost Basis']*portfolio[type]['Shares']))/(num_shares + portfolio[type]['Shares'])
                print(portfolio[type]['Cost Basis']) #delete this
                money -= allocated_money
                portfolio[type]['Shares'] += num_shares
                update_tranaction_log('TQQQ', num_shares, price, day)
            
        elif type == 'UnLeveraged':
            price = get_price(day, 'VOOG')
            num_shares = allocated_money / price
            if not num_shares < 0.05: 
                if portfolio[type]['Cost Basis'] == None:
                    portfolio[type]['Cost Basis'] = get_price(day, 'VOOG')                
                portfolio[type]['Cost Basis'] = (allocated_money + (portfolio[type]['Cost Basis']*portfolio[type]['Shares']))/(num_shares + portfolio[type]['Shares'])
                money -= allocated_money
                portfolio[type]['Shares'] += num_shares
                update_tranaction_log('VOOG', num_shares, price, day)
            
        else:
            print('There was an error with the type')
    return

def sell(type, percent_holdings, day):
    '''This function sells a percentage of the shares of a particular stock'''    
    global money
    if type == 'Leveraged':
        price = get_price(day, 'TQQQ')
        num_shares = percent_holdings * portfolio[type]['Shares']
        money += num_shares * price
        portfolio[type]['Shares'] -= num_shares
        #It is assumed that once any Leveraged stock is sold, the money will immediately be used to purchase an UnLeveraged stock (such as VOOG)
        buy('UnLeveraged', num_shares*price,day)
        if percent_holdings == 1:
            portfolio[type]['Cost Basis'] = 999999999
        else:
            portfolio[type]['Cost Basis'] = (portfolio[type]['Cost Basis'] + price)/2
        
    elif type == 'UnLeveraged':
        price = get_price(day, 'VOOG')
        num_shares = percent * portfolio[type]['Shares']
        money += num_shares * price
        portfolio[type]['Shares'] -= num_shares        
    else:
        print('There was an error with the type')
    return

def determine_action(day):
    '''This function determines whether to buy or sell stock (Leveraged or UnLeveraged)
    given data from the previous ten days woth of closing data
    '''
    global money
    action = None
    amount = None
    #if money > 50:
        #action = 'buy'
        #amount = 1
        #print('buy $1000 woth of TQQQ')

    if stock_data['TQQQ']['Adj Close'][day] / stock_data['TQQQ']['Adj Close'][day-25] <  0.5:
        action = 'buy'
        amount = 1
        print('50% decrease in 25 days')    
    if stock_data['TQQQ']['Adj Close'][day] / portfolio['Leveraged']['Cost Basis'] > 1.35:
        action = 'sell'
        amount = 0.1
        print('100% gain in value in TQQQ holdings')  
    if stock_data['TQQQ']['Adj Close'][day] / stock_data['TQQQ']['Adj Close'][day-1] > 1.15:
        action = 'sell'
        amount = 0.1
        print('15% one day increase')        
    if money > 1000:
        action = 'buy'
        amount = 1
        print('buy $1000 woth of TQQQ')

    return action, amount

def update_tranaction_log(ticker, num_shares, share_price, day):
    global transaction_number
    transaction_log[transaction_number] = '{} shares of {} were bought at ${} per share on day {}'.format(num_shares, ticker, share_price, day)
    transaction_number += 1
    return

#def update_active_log(type, ticker, num_shares, cost_basis):
    #active_log[str(type)][ticker]['number of shares'] = num_shares
    #active_log[str(type)][ticker]['cost basis'] = cost_basis
    #return

def simulation():
    global money
    global total_money_added
    buy('Leveraged', money, 34)
    for i in range(35,len(stock_data['TQQQ']['Adj Close'])-5):
        current_day = i
        action, amount = determine_action(current_day)
        if current_day % 15 == 0:
            money += 100
            total_money_added += 100
        if action == 'buy':
            buy('Leveraged', money * amount, current_day)
        if action == 'sell':
            sell('Leveraged',amount, current_day)
        leveraged_portfolio_value[current_day] = get_price(current_day, 'TQQQ') * portfolio['Leveraged']['Shares'] / (total_money_added)
        unleveraged_portfolio_value[current_day] = get_price(current_day, 'VOOG') * portfolio['UnLeveraged']['Shares'] / (total_money_added)
        money_value[current_day] = money
        sim_days[current_day] = current_day
        total_value[current_day] = get_price(current_day, 'TQQQ') * portfolio['Leveraged']['Shares']+ get_price(current_day, 'VOOG') * portfolio['UnLeveraged']['Shares']+ money
    return

def main():
    return

simulation()

fig1 = plt.figure()
plt.plot(sim_days,leveraged_portfolio_value, 'blue',label='TQQQ Holdings')
plt.plot(sim_days,unleveraged_portfolio_value, 'r',label='VOOG Holdings')
plt.plot(sim_days,unleveraged_portfolio_value+leveraged_portfolio_value, 'green',label='Total Portfolio')
plt.plot(sim_days,stock_data['VOOG']['Adj Close'][1:2279]/stock_data['VOOG']['Adj Close'][0], 'black',label='VOOG Price')
#plt.plot(sim_days,stock_data['TQQQ']['Adj Close'][1:2279]/stock_data['TQQQ']['Adj Close'][0], 'orange',label='TQQQ Price')
plt.title('Portfolio')
plt.xlabel('day')
plt.ylabel('Value')
plt.legend()
plt.show()

fig2 = plt.figure()
plt.plot(sim_days,total_value, 'green',label='total value')
plt.title('Portfolio')
plt.xlabel('day')
plt.ylabel('Value')
plt.legend()
plt.show()
