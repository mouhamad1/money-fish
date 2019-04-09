#!/usr/bin/python3
import requests
import time

url = 'http://localhost:5000' # 'https://money.fish'

key = 'db1579c949d0ff926571fb87fde937b1f93f4085'
# Register the player
r = requests.post(url + '/register', {'name': 'Robinson', 'key': key})
print(r.content)

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

    #Strat1
    if day ==1:
        if fish > 2:
            ask_size = fish - 2
            bid_size = 1 # to see where is the price
            ask = 1 #to win priority
            bid = 110 #to modify probably
            requests.post(url + '/order/%s' % key, {'shells': -bid})
            for i in range(ask_size):
                requests.post(url + '/order/%s' % key, {'shells': ask})
        else:
            bid_size = 2 - fish
            ask_size = 0
            bid = shells // 2 #to modify 
            for i in range(0,bid_size):
                requests.post(url + '/order/%s' % key, {'shells': -bid})
        bid_hist.append(bid)
        bid_size_hist.append(bid_size)
        ask_size_hist.append(ask_size)
    else:
        if fish > 2:
            ask_size = fish - 2
            bid_size = 1 # to see where is the price
            ask = 1 #to win priority
            #modify to take into account the population dynamic and my executions
            bid =  last_price + 1 #to modify probably 
            requests.post(url + '/order/%s' % key, {'shells': -bid})
            for i in range(ask_size):
                requests.post(url + '/order/%s' % key, {'shells': ask})
            bid_hist.append(bid)
        else:
            bid_size = 2 - fish
            if shells_hist[-1] != shells_hist[-2] + last_price * (ask_size_hist[-1] - bid_size_hist[-1]): #check if my orders were executed
                if villagers == villagers_hist[–2]: #no death
                    bid = min( 2 * max(prices_hist), shells-2) #2*ask - price
                    requests.post(url + '/order/%s' % key, {'shells': -bid})
                else: #some villagers died
                    bid =  min( 2 * max(prices_hist), shells) #2*ask - price
            else:# orders executed
                if villagers == villagers_hist[-2]: #no death
                    bid = min( bid_hist[-1] + 2,shells)
                else: #some villagers died
                    bid =  min( 2 * max(prices_hist), shells-2) #2*ask - price
            bid_hist.append(bid)
            for i in range(bid_size):
                requests.post(url + '/order/%s' % key, {'shells': -bid})

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


