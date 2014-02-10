# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 09:15:28 2013

@author: aitor
"""
import urllib2
import base64
import json
import time
import io
import os
import datetime

# TODO
USERNAME = ""
PASSWORD = ""

auth_string = base64.encodestring('%s:%s' % (USERNAME, PASSWORD))


    

def getCategories():
    req_url_tree= 'https://api.bbva.com/apidatos/info/merchants_categories.json'
    req = urllib2.Request(req_url_tree)
    req.add_header("Authorization", auth_string)
    response = urllib2.urlopen(req)
    res = response.read()    
    data = json.loads(res)
    cat_list = data['data']['categories']
    categories = set()
    for cat in cat_list:
        categories.add(cat['code'])
    return categories
    
def saveJson(filename, data):
    with io.open(filename, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))
    
  
def scrapCube():
    groups = ['week', 'month']
    zip_codes = [28, 8]
    categories = getCategories()
    url_cube_base = 'https://api.bbva.com/apidatos/zones/cards_cube.json?date_min=20120101000000&date_max=20140101235959&group_by={0}&category={1}&zipcode={2}&by=incomes'  
    scrap('cube', url_cube_base, groups, zip_codes, categories)
    
def scrapPatterns():
    groups = ['month']
    zip_codes = [28, 8]
    categories = getCategories()
    url_patterns_base = 'https://api.bbva.com/apidatos/zones/consumption_pattern.json?date_min=20120101000000&date_max=20141231000000&group_by={0}&category={1}&zipcode={2}&cards=bbva'
    scrap('patterns', url_patterns_base, groups, zip_codes, categories)
    
def scrapOrigin():
    groups = ['week', 'month']
    zip_codes = [28, 8]
    categories = getCategories()
    url_cube_base = 'https://api.bbva.com/apidatos/zones/customer_zipcodes.json?date_min=20120101000000&date_max=20140101235959&group_by={0}&category={1}&zipcode={2}&by=incomes'
    scrap('origin', url_cube_base, groups, zip_codes, categories)
    
                                
def scrap(api_method, base_url, groups, zip_codes, categories):
    for group in groups:
        for code in zip_codes:
            for r in range(0,1000):
                for category in categories:
                    zip_code = str((code*1000) + r)
                    if zip_code.startswith('8'):
                        zip_code =  '0' + zip_code
                    req_url = base_url.format(group, category, zip_code)
                    repeat = True
                    times = 0
                    while(repeat):
                        try:
                            file_path = './data/{0}-{1}-{2}-{3}.json'.format(api_method, group, category, zip_code)
                            if os.path.exists(file_path):
                                break
                            req = urllib2.Request(req_url)
                            req.add_header("Authorization", auth_string)
                            response = urllib2.urlopen(req)
                            res = response.read()    
                            data = json.loads(res)                            
                            saveJson(file_path, data)  
                            repeat = False
                        except urllib2.HTTPError as e:
                            print 'Error {0} ({1}:{2}): {3} '.format(str(e.code),datetime.datetime.now().hour, datetime.datetime.now().minute, req_url)
                            if (e.code == 404):
                                repeat = False      
                            else:
                                repeat = True
                                print '****** Waiting: {0}:{1}'.format(datetime.datetime.now().hour, datetime.datetime.now().minute)
                                print req_url
                                time.sleep(600)
                        except Exception as e:
                            print
                            print
                            print '*' * 20, "UNEXPECTED ERROR", '*' * 20
                            print
                            print req_url
                            print
                            print
                            print "Trying next one..."
                            print 
                            if times > 3:
                                repeat = False
                            times += 1
                            time.sleep(1800)
                            
                        
                        
                    
if __name__ == '__main__':
    print '*********************Starting scraping*********************\n'
    print '*********************Clients Cube*********************\n'
    scrapCube()
    print '*********************Consumption patterns*********************\n'
    scrapPatterns()
    print '*********************Top client origin zip code*********************\n'
    scrapOrigin()
    print '*********************Done*********************'
    
    
