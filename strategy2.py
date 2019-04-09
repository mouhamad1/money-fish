#!/usr/bin/python3
import requests
import time
import random
import math
import numpy as np
from numba import njit, prange

url = 'http://localhost:5000' # 'https://money.fish'

key = 'db1579c949d0ff926571fb87fde937b1f93f4085'
# Register the player
r = requests.post(url + '/register', {'name': 'Robinson', 'key': key})
print(r.content)

@njit(parallel=True)
def expected_fishes(N, day, theta0, mu=0.03, kappa=0.99, sigma=0.012, trials=1000):
    """expected number of fishers for the N villagers at day N"""
    def distrib(N, day, theta0, mu, kappa, sigma):
        """Return the number of fishes for the N villagers at day"""
        if day == 1:
            theta = random.normalvariate(mu, sigma / np.sqrt(1.0 - kappa ** 2))
        else:
            theta = random.normalvariate(mu + kappa * (theta0 - mu), sigma)
        fishes = 0
        for i in prange(N):
            u = random.random()
            fish = 0
            while u < 1.0 - math.exp(-np.exp(theta)):
                fish += 1
                u = random.random()
            fishes += fish
        return fishes
    distribs = []
    for i in prange(trials):
        distribs.append(distrib(N,day,theta0,mu,kappa,sigma))
    expected,standdev = mean(distribs),std(distribs)
    return expected,standdev

def get_theta0(N :int ,fishes :int) -> float:
    """Return the theta corresponding to a total of N villagers and a number fishes of fish
    fishes= N*(1-p)/p and p = exp(-exp(theta))
    ."""
    p = N / (fishes + N)
    return np.log(-np.log(p))

# Poll until start
day = 0
prices_hist = []
shells_hist =[]
traded_volume_hist = []
fish_hist = []
bid_hist = []
bid_size_hist = []
ask_size_hist = []
villagers_hist = []
theta0 = random.normalvariate(mu, sigma / np.sqrt(1.0 - kappa ** 2))
trial = 100
predicted_fishes = []
def place_orders(info):
    fish = info[key]['fish']
    shells =  info[key]['shells']
    last_price = info['last_price']
    last_price = last_price if last_price else 100
    villagers = info['villagers']
    traded_volume = info['last_quantity']
    traded_volume = traded_volume if traded_volume else 0
    day = info['day']
    prices_hist.append(last_price)
    shells_hist.append(shells)
    traded_volume_hist.append(traded_volume)
    fish_hist.append(fish)
    villagers_hist.append(villagers)

    #Strat2
    if day == 1:
        exp_fishes,std_fishes = expected_fishes(N=villagers,day=1,theta0=theta0)
        predicted_fishes.append(exp_fishes)
        sell_strong = (exp_fishes + 2*stsd_fishes/np.sqrt(trial) - 2*villagers < 0)
        sell_maybe = (exp_fishes - 2*stsd_fishes/np.sqrt(trial)<= 2 *villagers <=  exp_fishes + 2*std_fishes/np.sqrt(trial))
        if fish > 2:
            ask_size = fish - 2
            bid_size = 0 # to see where is the price
            if sell_strong:
                ask = 1000  #some villagers are obliged to buy
            elif sell_maybe:
                ask = 500 # a small number is obliged to buy
            else:
                ask = 1 # many sellers, so we target priority
            bid = 0 #We don't buy
            for i in range(ask_size): #depending on signal we post at different levels
                ask += -min(sell_strong*i*100,500) # to increase execution likelihood
                ask += sell_maybe*i*100*pow(-1,i%2) #a zone around 500 if we have doubts
                requests.post(url + '/order/%s' % key, {'shells': ask})
        else:
            bid_size = 2 - fish
            ask_size = 0
            bid = (bid_size >0) * shells // bid_size + 0 #we do ann all-in for better living odds
            for i in range(0,bid_size):
                requests.post(url + '/order/%s' % key, {'shells': -bid})
        bid_hist.append(bid)
        bid_size_hist.append(bid_size)
        ask_size_hist.append(ask_size)
    else:
        if villagers == villagers_hist[-2]:#no death 
                fishes_yesterday = max(2*villagers_hist[-2],predicted_fishes[-1])
                theta0 = get_theta0(N=villagers,fishes=fishes_yesterday)
        else :#some people died
                fishes_yesterday = 2*villagers
                theta0  =  get_theta0(N=villagers,fishes=fishes_yesterday)
        exp_fishes,std_fishes = expected_fishes(N=villagers,day=day,theta0=theta0)
        predicted_fishes.append(exp_fishes)
        sell_strong = (exp_fishes + 2*stsd_fishes/np.sqrt(trial) - 2*villagers < 0)
        sell_maybe = (exp_fishes - 2*stsd_fishes/np.sqrt(trial)<= 2 *villagers <=  exp_fishes + 2*std_fishes/np.sqrt(trial))
        if fish > 2:
            ask_size = fish - 2
            bid_size = 0 # to see where is the price
            if sell_strong:
                ask = max(last_price_hist) #some are obliged to buy
            elif sell_maybe:
                ask = last_price #a small wanna buy
            else:
                ask = 1 # target priority beacause there are many sellers
            bid = 0 
            for i in range(ask_size):
                ask += sell_strong*i*10*pow(-1,i%2)
                ask += sell_maybe*i*5*pow(-1,i%2)
                ask = max(1,ask)
                requests.post(url + '/order/%s' % key, {'shells': ask})
            bid_hist.append(bid)
        else:
            bid_size = 2 - fish
            bid = (bid_size > 0) * shells // bid_size + 0 #all-in to live 
            for i in range(0,bid_size):
                requests.post(url + '/order/%s' % key, {'shells': -bid})
            bid_hist.append(bid)

while True:
    try:
        info = requests.get(url + '/info/%s' % key)
        if info.status_code == 404:
            # had to leave the island
            print("bye bye")
            exit(0)
        info = info.json()
        if info['day'] > day:
            place_orders(info)
    except Exception as e:
        print(e)
    # wait
    time.sleep(1)


