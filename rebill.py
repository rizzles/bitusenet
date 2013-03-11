#!/usr/bin/python

import datetime
import time
import sys

from tornado.options import define, options
import tornado.database

import pymongo

import logging
import sys
import requests
import tornado.escape

define("mysql_user", default="nick", help="database user")
define("mysql_password", default="mohair94", help="database password")
define("users_host", default="10.114.97.213:3306", help="users database")
define("users_database", default="newzbeta", help="users name")

usersdb = tornado.database.Connection(
    host=options.users_host, database=options.users_database,
    user=options.mysql_user, password=options.mysql_password)

# Setup logging
LOG_FILENAME = "/home/ubuntu/bitusenet_rebill.txt"
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5242880, backupCount=5)
consolehandler = logging.StreamHandler()
consolehandler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.addHandler(consolehandler)

mongoconnection = pymongo.Connection('10.244.42.52', 27017)
mongobitusenet = mongoconnection.bitusenet
mongoaddresses = mongobitusenet.addresses
mongousers = mongobitusenet.bitusenet
mongoprice = mongobitusenet.price

users = mongousers.find()
now = datetime.datetime.now()


r = requests.get('http://bitcoincharts.com/t/weighted_prices.json')
  
prices = tornado.escape.json_decode(r.text)
for k,v in prices.iteritems():
    if k == 'USD':
        logging.info(v['24h'])
        charge = 13 / float(v['24h'])
        mongoprice.update({ "_id" : { '$exists' : True } }, {'USD':v['24h'], 'charge':charge})
        
        


sys.exit()
logger.info("%s"%now)
for user in users:
    created = datetime.datetime.strptime(user['created'], "%Y-%m-%d %H:%M:%S")
    activatedcheck = created + datetime.timedelta(hours=12)
    createdcheck = created + datetime.timedelta(days=30)

    if now > activatedcheck and user['active'] == False:
        logger.info("Bitcoin user %s hasn't sent a coin in 24 hours. Deleting"%user['username'])
        logger.info("")
        mongoaddresses.update({'address':user['address']},{'$set':{'used':False}})        
        mongousers.remove({'username':user['username']})

    if createdcheck < now:
        logger.info("Deleting user %s. Account expired"%user['username'])
        logger.info("")
        mongousers.remove({'username':user['username']})
        usersdb.execute("""DELETE FROM auth.logins WHERE username = %s""", user['username'])
