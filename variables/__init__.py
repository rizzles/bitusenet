import pymongo
import tornado.database


authdb = tornado.database.Connection(
    host='10.101.26.249', database='auth',
    user='nick', password='mohair94')

# using the itchy headers mongo db
mongoconnection = pymongo.Connection('ec2-50-17-28-132.compute-1.amazonaws.com', 27017)
mongodb = mongoconnection.bitusenet
