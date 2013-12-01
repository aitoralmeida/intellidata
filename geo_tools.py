# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 14:08:27 2013

http://stackoverflow.com/questions/15736995/how-can-i-quickly-estimate-the-distance-between-two-latitude-longitude-points

@author: aitor
"""

from math import radians, cos, sin, asin, sqrt
from bbvalib import create_mongoclient
import json

json_data=open('./data/all_zipcodes.json')
zipcodes = json.load(json_data)


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    km = 6367 * c
    return km
    
def update_distances():
    bbva = create_mongoclient()    
    weekly = bbva.top_clients_week 
    all_transactions = weekly.find()
    
    for transaction in all_transactions:
        home_lat, home_lon = get_lon_lat(transaction['home_zipcode'])
        shop_lat, shop_lon = get_lon_lat(transaction['shop_zipcode'])
        distance = haversine(home_lon, home_lat, shop_lon, shop_lat)
        
def get_lon_lat(zipcode):
    result = zipcodes.get(zipcode)
    if result is not None:
        lat, lon = result
    else:
        lat = 47.66
        lon = -1.58
        
    return float(lat), float(lon)
    
    