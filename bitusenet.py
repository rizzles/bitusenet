#!/usr/bin/python

import logging
import os
import string
import random
import time
import hashlib
import uuid
import re
import datetime

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.options
import tornado.httpclient
import tornado.gen

from variables import *
import emailer

LOGFILE = '/var/log/bitusenet/bitusenet.log'
LOGLEVEL = logging.INFO
TOKEN = "27026cd1ab483989a80712e4a3431b159c597b02"

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/signup", SignupHandler),
            (r"/success", SuccessHandler),
            (r"/reset", ResetHandler),
            (r"/passwordreset", ActualResetHandler),
            (r"/resetsent", ResetSentHandler),            
            (r"/dashboard", DashboardHandler),
            (r"/contact", ContactHandler),
            (r"/faq", FAQHandler),
            (r"/google4a97efb83d0a5d8f.html", GoogHandler),
            (r"/callback", CallbackHandler),
            (r".*", A404Handler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="92oP7zEYxAB4YGkL3gUmGerJFuYhjEQnp3XdTP9oxc1=",
            site_name='bitusenet',
            login_url='/login',
            autoescape=None,
            debug=False,
            gzip=True
            )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.mongodb = mongodb


class BaseHandler(tornado.web.RequestHandler):
    @property
    def mongodb(self):
        return self.application.mongodb

    def get_current_user(self):
        user = self.get_cookie('bitusenet')
        if not user:
            return None
        collection = self.mongodb.bitusenet
        user = collection.find_one({'username': user})
        return user

    def write_error(self, status_code, exc_info=None, **kwargs):
        if status_code == 500:
            logging.error("500 error. Big problem")
            self.render('500.html', title="Bitusenet - Error")
        else:
            self.render('404.html', title="Bitusenet - Error")

    def write_error(self, status_code, **kwargs):
        if status_code == 500:
            logging.error("500 error. Big problem")
            self.render('500.html', title="Bitusenet - Error")
        else:
            self.render('404.html', title="Bitusenet - Error")


class ResetHandler(BaseHandler):
    def get(self):
        self.render('reset.html', errors=None)

    def post(self):
        email = self.get_argument('email', None)
        if not email:
            self.render('reset.html', errors='emailempty')
            return

        collection = self.mongodb.bitusenet
        user = collection.find_one({'email':email})
        
        if not user:
            logging.error('password reset requested for unknown email address')
            self.redirect("/resetsent")
            return

        if user['active'] == False:
            logging.error('password reset requested for unknown email address')
            self.redirect("/resetsent")
            return

        resetid = uuid.uuid4().hex
        collection.update({'email':email}, {"$set": {'resetid':resetid, 'resettime':time.time()}})
        emailer.send_user_password(email, resetid)

        self.redirect('/resetsent')


class ResetSentHandler(BaseHandler):
    def get(self):
        self.render('resetsent.html')


class ActualResetHandler(BaseHandler):
    def get(self):
        logging.info('password reset link from email received')
        id = self.get_argument('id', None)
        
        if not id:
            logging.error('no id was included with password reset request')
            self.redirect('/reset')
            return

        collection = self.mongodb.bitusenet
        user = collection.find_one({'resetid':id})

        if not user:
            logging.error('password reset id not found in database')
            self.redirect('/reset')
            return

        age = time.time() - user['resettime']
        # request is over an hour old.
        if age > 3600:
            logging.error('password reset link is over an hour old')
            self.render('resetexpired.html')
            return

        self.render('actualreset.html', errors=None, resetid=id)

    def post(self):
        resetid = self.get_argument("resetid", None)
        newpassword = self.get_argument("password", None)

        if not resetid:
            logging.error('No resetid sent along with password reset attempt')
            self.redirect('/reset')
            return

        if not newpassword:
            logging.error('No password sent along with password reset attempt')
            self.render('actualreset.html', errors="passwordempty", resetid=resetid)
            return

        collection = self.mongodb.bitusenet
        user = collection.find_one({'resetid': resetid})
        
        if not user:
            logging.error('Could not fint resetid associated to any users')
            self.redirect('/reset')
            return

        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(salt + newpassword).hexdigest()

        collection.update({"_id":user['_id']}, {"$set": {'resetid':None, 'resettime':None, 'salt':salt, 'password':hashed_password, 'raw':newpassword}})
        authdb.execute("""UPDATE auth.logins SET password = %s WHERE username = %s""", newpassword, user['username'])        

        self.redirect('/login')

class HomeHandler(BaseHandler):
    def get(self):
        self.render('index.html')


class DashboardHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('dashboard.html')


class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html', errors=None)

    def post(self):
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)

        collection = self.mongodb.bitusenet
        users = collection.find({'username': username})

        # match salted password
        for user in users:
            salt = user['salt']
            hashed_password = hashlib.sha512(salt + password).hexdigest()
            if hashed_password == user['password']:
                self.set_cookie('bitusenet', username)
                self.redirect("/dashboard")
                return

        logging.info("Could not match email or password on login")
        self.render("login.html", errors="notfound")
        

class SignupHandler(BaseHandler):
    def get(self):
        aff = self.get_argument('aff', None)
        self.render('signup.html', errors=None, aff=aff)

    def post(self):
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        email = self.get_argument('email', None)
        aff = self.get_argument('aff', None)
        
        if not username:
            self.render('signup.html', errors="usernameempty")
            return
        if not password:
            self.render('signup.html', errors="passwordempty")
            return

        usercoll = self.mongodb.bitusenet
        addresscoll = self.mongodb.addresses

        # Check to see if username already exists
        exists = usercoll.find_one({'username': username})
        if exists:
            logging.error('username exists on website')
            self.render('signup.html', errors="usernameexists")
            return

        # Check if username exists in auth db.
        exists = authdb.get("""SELECT * FROM auth.logins WHERE username = %s LIMIT 1""", username)
        if exists:
            logging.error('username exists in auth db.')
            self.render('signup.html', errors="usernameexists")
            return

        # password salt and hash
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(salt + password).hexdigest()

        # find free bitcoin address to associate with user
        btcaddress = addresscoll.find_one({'used':False})
        if not btcaddress:
            self.send_error()
            return

        user = {'password': hashed_password,
                'salt': salt,
                'raw': password,
                'username': username,
                'email': email,
                'active': False,
                'address': btcaddress['address'],
                'created': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                'aff': aff
                }
        usercoll.insert(user)
        addresscoll.update({'address':btcaddress['address']},{'$set':{'used':True}})

        self.set_cookie('bitusenet', username)
        self.redirect("/success")


class SuccessHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        if not self.current_user['address']:
            self.send_error()
            logging.error("No btc address associated with users account. No addresses free?")
            return
        self.render('success.html', address=self.current_user['address'])


class CallbackHandler(BaseHandler):
    def check_xsrf_cookie(self):
        pass

    def post(self):
        logging.info("callback request coming in")
        data = self.request.body
        json_data = tornado.escape.json_decode(data)

        address = json_data[u'signed_data'][u'address']
        tx_hash = json_data[u'signed_data'][u'txhash']
        address = json_data[u'signed_data'][u'address']
        created = json_data[u'signed_data'][u'created']
        confirmations = json_data[u'signed_data'][u'confirmations']
        userdata = json_data[u'signed_data'][u'userdata']
        amount = json_data[u'signed_data'][u'amount']
        agent = json_data[u'signed_data'][u'agent']
        amount_btc = json_data[u'signed_data'][u'amount_btc']
        signature = json_data[u'signature']

        sigstring = address + agent + str(amount) + str(amount_btc)+ str(confirmations) + created + str(userdata) + str(tx_hash) + TOKEN

        my_sig = hashlib.md5(sigstring).hexdigest()

        addresscoll = self.mongodb.addresses
        usercoll = self.mongodb.bitusenet

        if my_sig == signature:
            logging.info("signatures matched, request is from bitcoinmonitor.net")
            dbaddress = addresscoll.find_one({'address':address})
            if not dbaddress:
                logging.error("could not find bitcoin address in our mongodb that matched the one bitcoinmonitor.net sent %s", address)
                return
            user = usercoll.find_one({'address':address})
            if not user:
                logging.error("could not find bitcoin address %s associated with user", address)
                return

            # check total sent == 1 btc
            """
            total = int(dbaddress['amount']) + int(amount)
            if total < 100000000:
                logging.error("amount received was not a full bitcoin. %s - %s", amount, user['username'])
                addresscoll.update({'address':address},{'$set':{'amount':total}})
                return
            """
            # everything is good to go. found matching bitcoin addresses
            addresscoll.update({'address':address}, {'$set':{'used':False, 'amount':0}})

            # insert username and password into auth database
            authdb.execute("""INSERT INTO auth.logins(id, username, password, canpost) VALUES(1, %s, %s, 'n')""", user['username'], user['raw'])
            
            # update users account to active
            usercoll.update({'username':user['username']}, {'$set':{'active':True, 'address':None}})

            logging.info("Success. User %s sent 1 bitcoin. Accout activated", user['username'])


class FAQHandler(BaseHandler):
    def get(self):
        self.render('faq.html')


class ContactHandler(BaseHandler):
    def get(self):
        self.render('contact.html')


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('bitusent')
        self.clear_all_cookie()
        self.redirect('/')


class GoogHandler(BaseHandler):
    def get(self):
        self.render("google4a97efb83d0a5d8f.html")


class A404Handler(BaseHandler):
    def get(self):
        self.render('404.html', title="Bitusenet - Not Found")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie('bitusenet')
        self.clear_all_cookies()
        self.redirect('/')


def main():
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    tornado.options.parse_command_line()
    logging.info('Starting web server')

    main()

