#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import ssl
from re import findall
from urllib import quote_plus

CONNECT_TIMEOUT = 20


class Auth():
    def __init__(self, server, debuglevel=0, three_steps_auth=False):
        self.server = server
        self.three_steps_auth = three_steps_auth
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        handler = urllib2.HTTPSHandler(debuglevel=debuglevel, context=ctx)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)


    def get_id(self):
        print self.server
        data = urllib2.urlopen(self.server, timeout=CONNECT_TIMEOUT).read()
        auth_id = findall('<input type="hidden" name="ID" value="(.*)">', data)[0]
        self.auth_id = auth_id
        return auth_id

    def login(self, username, password):
        try:
            auth_id = self.get_id()
        except urllib2.URLError, e:
            print e
            return -1
        except urllib2.HTTPError, e:
            print e
            return -1
        if username is None or password is None:
            return -1
        if self.three_steps_auth :
            post_data = "ID=%s&STATE=%d&DATA=%s" % (auth_id, 1,quote_plus(username))
            auth_result = urllib2.urlopen(self.server, post_data).read()
            print auth_result
            post_data = "ID=%s&STATE=%d&DATA=%s" % (auth_id, 2,quote_plus(password))     
            auth_result = urllib2.urlopen(self.server, post_data).read()
            print auth_result
            if 'authenticated by' not in auth_result:
                return -2                    
            post_data = "ID=%s&STATE=%d&DATA=%s" % (auth_id, 3, 1)
            auth_result = urllib2.urlopen(self.server, post_data).read()
        else:
            post_data = "ID=%s&STATE=%d&DATA=%s&DATA=%s" % (auth_id, 0,
                quote_plus(username), quote_plus(password))
            auth_result = urllib2.urlopen(self.server, post_data).read()
            print auth_result
            if 'authenticated by' not in auth_result:
                return -2        
            post_data = "ID=%s&STATE=%d&DATA=%s" % (auth_id, 1, "1")
            auth_result = urllib2.urlopen(self.server, post_data).read()
            if 'User authorized for standard services' not in auth_result:
                return -3
        return 0
