import datetime
import time
import sys

from tornado.options import define, options
import tornado.database

import pymongo

mongoconnection = pymongo.Connection('10.244.42.52', 27017)
mongobitusenet = mongoconnection.bitusenet
mongoaddresses = mongobitusenet.addresses
mongousers = mongobitusenet.bitusenet

users = mongousers.find()
now = datetime.datetime.now()

print ""
for user in users:
    created = datetime.datetime.strptime(user['created'], "%Y-%m-%d %H:%M:%S")
    activatedcheck = created + datetime.timedelta(days=1)
    createdcheck = created + datetime.timedelta(days=30)

    if now > activatedcheck and user['active'] == False:
        print "Bitcoin user %s hasn't sent a coin in 24 hours. Deleting"%user['username']
        print ""
        mongoaddresses.update({'address':user['address']},{'$set':{'used':False}})        
        mongousers.remove({'username':user['username']})

    if createdcheck < now:
        print "Deleting user %s. Account expired"%user['username']
        print ""
        mongousers.remove({'username':user['username']})
