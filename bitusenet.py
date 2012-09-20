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

LOGFILE = '/var/log/bitusenet/bitusenet.log'
LOGLEVEL = logging.INFO

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="92oP7zEYxAB4YGkL3gUmGerJFuYhjEQnp3XdTP9oxco=",
            site_name='bitusenet',
            login_url='/login',
            autoescape=None,
            debug=True,
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
        if len(user) > 4:
            user = self.get_secure_cookie('bitusenet')
        if not user:
            return None
        collection = self.mongodb.users
        user = collection.find_one({'bitusenet': user})
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


class HomeHandler(BaseHandler):
    def get(self):
        self.render('index.html', title="Bitusenet - Bitcoin Usenet Access")


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

