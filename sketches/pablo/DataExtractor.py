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

req_url_patterns = 'https://api.bbva.com/apidatos/zones/consumption_pattern.json?date_min=20010101000000&date_max=20141231000000&group_by=month&zipcode=28013&cards=bbva'

req_url_top = 'https://api.bbva.com/apidatos/zones/customer_zipcodes.json?date_min=20010101000000&date_max=20140101235959&group_by=month&category=all&zipcode=28039&by=incomes'

#req = urllib2.Request(req_url_top)
#req.add_header("Authorization", auth_string)
#response = urllib2.urlopen(req)
#data = response.read()
#print data

import json, pprint

def print_labels(zipcode):
    zipcodes = set()
    req = urllib2.Request("https://api.bbva.com/apidatos/zones/customer_zipcodes.json?date_min=20010101000000&date_max=20140101235959&group_by=month&category=all&zipcode=%s&by=incomes" % zipcode)
    req.add_header("Authorization", auth_string)
    contents = json.load(urllib2.urlopen(req))
    for stat in contents['data']['stats']:
       for zc in stat['zipcodes']:
           zipcodes.add(zc['label'])
    print sorted(zipcodes)

#print
#print_labels("28039")
#print 
#print_labels("28232")
#print
#print_labels("28013")
#print 
print_labels("28018")
print


req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20130901235959&group_by=month&category=all&latitude=40.41988&longitude=-3.70830&zoom=2&by=incomes'


req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20130901235959&group_by=month&category=all&latitude=40.41962&longitude=-3.70809&zoom=2&by=incomes'

req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20130901235959&group_by=month&category=all&latitude=40.41952&longitude=-3.70560&zoom=2&by=incomes'

req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20130901235959&group_by=month&category=all&latitude=40.41934&longitude=-3.70349&zoom=2&by=incomes'

req_url_cube = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20130901235959&group_by=month&category=all&latitude=40.41938&longitude=-3.70661&zoom=2&by=incomes'

# req = urllib2.Request(req_url_cube)
# req.add_header("Authorization", auth_string)
# response = urllib2.urlopen(req)
# data = response.read()
# pprint.pprint(json.loads(data))



