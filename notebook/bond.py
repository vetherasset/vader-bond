#!/usr/bin/env python
# coding: utf-8

# In[3]:


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
    def __init__(self, timestamp=now(), number=0):
        self.timestamp = timestamp
        self.number = number

    def inc(self, n=1):
        self.number += n
        self.timestamp += n * 14


DECIMALS = 18
PRINCIPAL_DECIMALS = 18


class Token:
    def __init__(self, totalSupply=0):
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
            "max_debt": terms["max_debt"],
        }

        self.total_debt = initial_debt
        self.last_decay = block.number

        # adjustment
        self.adjustment = {
            "add": adj["add"],
            "rate": adj["rate"],
            "target": adj["target"],
            "buffer": adj["buffer"],
            "last_block": adj["last_block"],
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

    # view
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

BLOCKS_PER_HOUR = 270
VADER_TOTAL_SUPPLY = (25 * 10 ** 9) * 10 ** DECIMALS
SALE = 10 ** 7 * 10 ** DECIMALS

LP_PRICE_USD = 23.29
VADER_PRICE_USD = 0.03
DISCOUNT = 0.94
MAX_LP = 1100 * 10 ** PRINCIPAL_DECIMALS

# --- min price ---
# amount of VADER to receive per LP
v = LP_PRICE_USD / (VADER_PRICE_USD * DISCOUNT)

# amount of LP to buy 1 Vader
x = 1 / v
min_price = x * 10 ** PRINCIPAL_DECIMALS

# --- control variable ---
# initial number of LP to receive before bond price exceeds min price
D = 10000
control_variable = min_price * (VADER_TOTAL_SUPPLY / (10 ** DECIMALS)) / D

# --- vesting terms ---
vesting_terms = BLOCKS_PER_HOUR * 24 * 14

# --- max payout % (100% = 1e5) ---
max_payout = math.ceil(MAX_LP * v / VADER_TOTAL_SUPPLY * 1e5)

# --- max debt ---
max_debt = (25 * 10 ** 6) * 10 ** DECIMALS
assert VADER_TOTAL_SUPPLY * max_payout / 1e5 <= max_debt * 1.0

# --- terms ---
terms = {
    "control_variable": control_variable,
    "vesting_terms": vesting_terms,
    "min_price": min_price,
    "max_payout": max_payout,
    "max_debt": max_debt,
}

adj = {"add": False, "rate": 0, "target": 0, "buffer": 0, "last_block": 0}

print(terms)


# In[22]:


block = Block()
payoutToken = Token(VADER_TOTAL_SUPPLY)
treasury = Treasury()

initial_debt = 0

b = Bond(block, payoutToken, treasury, initial_debt, terms, adj)

# graph
from matplotlib import pyplot as plt
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
N = BLOCKS_PER_HOUR * 24
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

    if sold < SALE and random() > 0.9 and b.bond_price() <= 1.07 * market_price:
        r = random()
        amount = r * MAX_LP
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


def sample(s):
    n = len(prices)
    if s <= 0:
        return

    _s = n / s

    print("--- block | price | market price | amount | payout | sold | % sold---")

    for i in range(n):
        if i % _s == 0:
            price = prices[i] / 10 ** PRINCIPAL_DECIMALS
            amount = amounts[i] / 10 ** PRINCIPAL_DECIMALS
            payout = payouts[i] / 10 ** DECIMALS
            market_price = market_prices[i] / 10 ** PRINCIPAL_DECIMALS
            total_payout = total_payouts[i] / 10 ** DECIMALS
            percent_sold = total_payout * 10 ** DECIMALS / SALE * 100
            print(
                f"{i} | {price:.6f} | {market_price:.6f} | {amount:.2f} | {payout:.2f} | {total_payout:.2f} | {percent_sold:.2f}"
            )


print(f"num buyers: {num_buyers}")
sample(10)

print("--- price ---")
plt.plot(xs, prices)
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


# In[ ]:
