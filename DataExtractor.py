# -*- coding: utf-8 -*-
"""
Created on Fri Oct 04 10:17:03 2013

@author: aitor
"""

import urllib2
import base64

auth_string = base64.encodestring('inteli-data:3d0a44dd75147adb9b3afdfab229aada36eee79a')
req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20130101000000&date_max=20130101235959&group_by=month&category=all&zipcode=28013&by=incomes'
req_url_patterns = 'https://api.bbva.com/apidatos/zones/consumption_pattern.json?date_min=20130101000000&date_max=20131231000000&group_by=month&zipcode=28013&cards=bbva'
req_url_top = 'https://api.bbva.com/apidatos/zones/customer_zipcodes.json?date_min=20130101000000&date_max=20130101235959&group_by=month&category=all&zipcode=28013&by=incomes'
req_url_tree= 'https://api.bbva.com/apidatos/info/merchants_categories.json'

req = urllib2.Request(req_url_patterns)
req.add_header("Authorization", auth_string)
response = urllib2.urlopen(req)
data = response.read()
print data