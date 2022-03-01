#!/usr/bin/env python
# coding: utf-8

# In[1]:


# !pip install matplotlib
# !pip install numpy
# !pip install prettytable


# In[1]:


from datetime import datetime

def now():
    return datetime.now().timestamp()


def tx(func):
    def inner(*args, **kwargs):
        self = args[0]
        self.block.inc()
        return func(*args, **kwargs)
    return inner


class Block:
    def __init__(self, timestamp = now(), number = 0):
        self.timestamp = timestamp
        self.number = number
     
    def inc(self, n = 1):
        self.number += n
        self.timestamp += n * 14

DECIMALS = 18
PRINCIPAL_DECIMALS = 18


class Token:
    def __init__(self, totalSupply = 0):
        self.totalSupply = totalSupply


class Treasury:
    def __init__(self):
        pass
    
    # view
    def value_of_token(self, amount):
        return amount


class Bond:
    def __init__(self, block, payoutToken, treasury, initial_debt, terms, adj):
        self.block = block
        self.payoutToken = payoutToken
        self.treasury = treasury
        
        # terms
        assert terms["control_variable"] > 0
        assert terms["vesting_terms"] >= 10000
        assert terms["max_payout"] <= 1000
        
        self.terms = {
            "control_variable": terms["control_variable"],
            "vesting_term": terms["vesting_terms"],
            "min_price": terms["min_price"],
            "max_payout": terms["max_payout"],
            "max_debt": terms["max_debt"]
        }

        self.total_debt = initial_debt
        self.last_decay = block.number

        # adjustment
        self.adjustment = {
            "add": adj["add"],
            "rate": adj["rate"],
            "target": adj["target"],
            "buffer": adj["buffer"],
            "last_block": adj["last_block"]
        }

    # view
    def debt_decay(self):
        block_since_last = self.block.number - self.last_decay
        decay = self.total_debt * block_since_last / self.terms["vesting_term"]
        if decay > self.total_debt:
            decay = self.total_debt
        return decay

    def decay_debt(self):
        self.total_debt -= self.debt_decay()
        self.last_decay = self.block.number

    # view
    def current_debt(self):
        return self.total_debt - self.debt_decay()
    
    # view
    def debt_ratio(self):
        return self.current_debt() * 10 ** 18 / self.payoutToken.totalSupply
    
    #view
    def bond_price(self):
        price = self.terms["control_variable"] * self.debt_ratio() / 10 ** 18
        if price < self.terms["min_price"]:
            price = self.terms["min_price"]
        return price

    # view
    def payout_for(self, value):
        return (value * 10 ** PRINCIPAL_DECIMALS) / self.bond_price()

    # view
    def max_payout(self):
        return self.payoutToken.totalSupply * self.terms["max_payout"] / 1e5
    
    def adjust(self):
        block_can_adjust = self.adjustment["last_block"] + self.adjustment["buffer"]
        rate = self.adjustment["rate"]
        if rate != 0 and self.block.number >= block_can_adjust:
            initial = self.terms["control_variable"]
            if self.adjustment["add"]:
                self.terms["control_variable"] += rate
                if self.terms["control_variable"] >= self.adjustment["target"]:
                    self.adjustment["rate"] = 0
            else:
                self.terms["control_variable"] -= rate
                if self.terms["control_variable"] <= self.adjustment["target"]:
                    self.adjustment["rate"] = 0

            self.adjustment["last_block"] = self.block.number
    
    @tx
    def deposit(self, amount):
        self.decay_debt()
        assert self.total_debt < self.terms["max_debt"]
        
        value = self.treasury.value_of_token(amount)
        payout = self.payout_for(value)
        
        assert payout >= 10 ** DECIMALS / 100
        assert payout <= self.max_payout()
        
        self.total_debt += value
        
        price = self.bond_price()
        if price > self.terms["min_price"] and self.terms["min_price"] > 0:
            self.terms["min_price"] = 0
        
        self.adjust()
        
        return payout


# In[16]:


import math
import json

BLOCKS_PER_HOUR = 270
VADER_TOTAL_SUPPLY = (25 * 1e9) * 10 ** DECIMALS
SALE = 50 * (1e6) * (10 ** DECIMALS)
VESTING_DAYS = 21

TOKEN_PRICE_USD = 3000.00
VADER_PRICE_USD = 0.055
DISCOUNT = 0.90
MAX_USD = 5 * 1e5
MAX_TOKEN_PER_DEPOSIT = MAX_USD / TOKEN_PRICE_USD * 10 ** PRINCIPAL_DECIMALS

# --- min price ---
# amount of VADER to receive per token
v = TOKEN_PRICE_USD / (VADER_PRICE_USD * DISCOUNT)

# amount of token to buy 1 Vader
x = 1 / v
min_price = x * 10 ** PRINCIPAL_DECIMALS

# --- control variable ---
# bond price = control variable * debt ratio / 1e18
# debt ratio = current debt * 1e18 / total supply of Vader
# current debt <= total amount of token to receive
# 
# cv = control variable
# V = total supply of Vader
# d = current debt
# D = max total debt
#
# d <= D
# bond price = cv * d / V
#
# min bond price <= cv * D / V
#
# initial amount of token to receive before bond price exceeds min price
D = min_price * SALE / 10 ** DECIMALS
# cv = Vader total supply / SALE
control_variable = min_price * VADER_TOTAL_SUPPLY / D

# --- vesting terms ---
vesting_terms = BLOCKS_PER_HOUR * 24 * VESTING_DAYS

# --- max payout % (100% = 1e5) ---
max_payout = math.ceil(MAX_TOKEN_PER_DEPOSIT * v / VADER_TOTAL_SUPPLY * 1e5)

# --- max debt ---
max_debt = SALE
assert VADER_TOTAL_SUPPLY * max_payout / 1e5 <= max_debt * 1.0

# --- terms ---
terms = {
    "control_variable": control_variable,
    "vesting_terms": vesting_terms,
    "min_price": min_price,
    "max_payout": max_payout,
    "max_debt": max_debt
}

adj = {
    "add": False,
    "rate": 0,
    "target": 0,
    "buffer": 0,
    "last_block": 0
}

print("Max token per deposit:", MAX_TOKEN_PER_DEPOSIT / 10 ** PRINCIPAL_DECIMALS)
print("Min token before price > min price:", D / 10 ** PRINCIPAL_DECIMALS)
print("Min price:", terms["min_price"] / 10 ** PRINCIPAL_DECIMALS)
print("Price:", terms["control_variable"] * D / VADER_TOTAL_SUPPLY / 10 ** PRINCIPAL_DECIMALS)
print("terms:", json.dumps(terms, indent=2))


# In[17]:


block = Block()
payoutToken = Token(VADER_TOTAL_SUPPLY)
treasury = Treasury()

initial_debt = 0

b = Bond(block, payoutToken, treasury, initial_debt, terms, adj)

# graph
from matplotlib import pyplot as plt
from prettytable import PrettyTable
from random import random, randint

# store for graph
prices = []
amounts = []
payouts = []
market_prices = []
control_vars = []
debt_ratios = []
total_debts = []

# num blocks
N = BLOCKS_PER_HOUR * 24 * 3
market_price = min_price
sold = 0
num_buyers = 0
for i in range(N):
    amount = 0
    payout = 0
    
    # get bond price before buy
    prices.append(b.bond_price())
    
    if random() > 0.499:
        market_price = min(market_price * 1.01, 1000 * min_price)
    else:
        market_price *= 0.99

    market_price = min_price
    
    if sold < SALE and random() > 0.9 and b.bond_price() <= 1.05 * market_price:
        r = random()
        amount = r * MAX_TOKEN_PER_DEPOSIT
        value = treasury.value_of_token(amount)
        payout = b.payout_for(value)
        
        if payout < 10 ** DECIMALS / 100 or payout >= b.max_payout():
            payout = 0
            amount = 0
            block.inc(1)
        else:
            payout = b.deposit(amount)
            sold += payout
            num_buyers += 1
    else:
        block.inc(1)
    
    payouts.append(payout)
    amounts.append(amount)
    market_prices.append(market_price)
    control_vars.append(b.terms["control_variable"])
    debt_ratios.append(b.debt_ratio())
    total_debts.append(b.total_debt)

xs = [i for i in range(N)]

total_payouts = []
total_payout = 0
for p in payouts:
    total_payout += p
    total_payouts.append(total_payout)

price_changes = []
p0 = 0
for p in prices:
    dp = 0
    if p0 > 0:
        dp = (p - p0) / p0
    price_changes.append(dp)
    p0 = p

def sample(f = lambda i: True):
    n = len(prices)

    table = PrettyTable()
    table.field_names = ["block", "price", "price change %", "market price", "amount", "payout", "sold", "% sold"]
    
    for i in range(n):
        if f(i):
            price = prices[i] / 10 ** PRINCIPAL_DECIMALS
            price_change = price_changes[i] * 100
            amount = amounts[i] / 10 ** PRINCIPAL_DECIMALS
            payout = payouts[i] / 10 ** DECIMALS
            market_price = market_prices[i] / 10 ** PRINCIPAL_DECIMALS
            total_payout = total_payouts[i] / 10 ** DECIMALS
            percent_sold = total_payout * 10 ** DECIMALS / SALE * 100
            table.add_row([
                i,
                f'{price:.6f}',
                f'{price_change:.4f}',
                f'{market_price:.6f}',
                f'{amount:.2f}',
                f'{payout:.2f}',
                f'{total_payout:.2f}',
                f'{percent_sold:.2f}'
            ])

    print(table)

print(f'num buyers: {num_buyers}')

# sample(lambda i: i % (N / 10) == 0)
sample(lambda i: price_changes[i] > 0 or payouts[i] > 0)
            
print("--- price ---")
plt.plot(xs, prices) 
plt.show()

print("--- price change ---")
plt.plot(xs, price_changes) 
plt.show()

print("--- total payout ---")
plt.plot(xs, total_payouts) 
plt.show()

print("--- payout ---")
plt.plot(xs, payouts) 
plt.show()

print("--- amount ---")
plt.plot(xs, amounts) 
plt.show()

print("--- market price ---")
plt.plot(xs, market_prices) 
plt.show()

print("--- control variable ---")
plt.plot(xs, control_vars) 
plt.show()

print("--- debt ratio ---")
plt.plot(xs, debt_ratios) 
plt.show()

print("--- total debt ---")
plt.plot(xs, total_debts) 
plt.show()

