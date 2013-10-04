# -*- coding: utf-8 -*-
"""
Created on Fri Oct 04 10:17:03 2013

@author: aitor
"""

import urllib2
import base64

auth_string = base64.encodestring('inteli-data:3d0a44dd75147adb9b3afdfab229aada36eee79a')
req_url = 'http://www.someserver.com/somepath/somepage.html'

req = urllib2.Request(req_url)
req.add_header("Authorization", auth_string)
response = urllib2.urlopen(req)
data = response.read()