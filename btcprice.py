#!/usr/bin/python

import pymongo
import requests
import logging
import tornado.escape

mongoconnection = pymongo.Connection('10.244.42.52', 27017)
mongobitusenet = mongoconnection.bitusenet
mongoprice = mongobitusenet.price

#r = requests.get('https://mtgox.com/api/1/BTCUSD/ticker')
r = requests.get('https://coinbase.com/api/v1/prices/sell')

  
prices = tornado.escape.json_decode(r.text)

price = prices['total']['amount']
charge = 11/float(price)

print price
print charge

mongoprice.update({ "_id" : { '$exists' : True } }, {'USD':price, 'charge':charge})
