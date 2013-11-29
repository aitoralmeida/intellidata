# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 09:14:17 2013

@author: aitor
"""

import networkx as nx
from networkx.readwrite import gexf
import json
from networkx.algorithms import bipartite
import community

from bbvalib import create_mongoclient
from geo_tools import haversine

json_data=open('./data/all_zipcodes.json')
zipcodes = json.load(json_data)
json_data.close() 

def show_info(G):
    print 'Is directed?: %s' %(str(G.is_directed())) 
    print 'Nodes: %i' % (len(G.nodes()))
    print 'Edges: %i' % (len(G.edges()))
    
def export_gexf(G, path):
    gexf.write_gexf(G, path)    

#def get_total_relations():    
#    G = nx.DiGraph()
#    bbva = create_mongoclient()
#    
#    weekly = bbva.top_clients_week
#    # all_transactions = weekly.find({ 'category' : 'es_barsandrestaurants' })
#    all_transactions = weekly.find()
#    for transaction in all_transactions:
#        G.add_edge( transaction['home_zipcode'], 
#                    transaction['shop_zipcode'], 
#                    weight=transaction['incomes'], 
#                    incomes=transaction['incomes'], 
#                    num_payments=transaction['num_payments'])
#    show_info(G)
#    return G
    
def get_total_relations(min_km = 0):    
    bbva = create_mongoclient()    
    weekly = bbva.top_clients_week  
    
    G = nx.DiGraph()
    all_transactions = weekly.find()
    for transaction in all_transactions:
        home_lat, home_lon = get_lon_lat(transaction['home_zipcode'])
        shop_lat, shop_lon = get_lon_lat(transaction['shop_zipcode'])
        distance = haversine(home_lon, home_lat, shop_lon, shop_lat)

        if distance > min_km:
            G.add_edge( transaction['home_zipcode'], 
                        transaction['shop_zipcode'], 
                        weight=transaction['incomes'], 
                        incomes=transaction['incomes'], 
                        num_payments=transaction['num_payments'])
    show_info(G)
    return G
    
def get_lon_lat(zipcode):
    result = zipcodes.get(zipcode)
    if result is not None:
        lat, lon = result
    else:
        lat = 47.66
        lon = -1.58
        
    return float(lat), float(lon)
    
def get_relations_by_category(week, category, min_km = 0):
    bbva = create_mongoclient()
    summary = bbva.top_clients_summary
    all_transactions = summary.find()
    G = nx.DiGraph()
    for transaction in all_transactions:
        shop_zipcode = transaction['_id']
        home_info = transaction['value']['home_zipcodes']    
        for key in home_info.keys():
            home_zipcode = key
            incomes = home_info[key]['per_week'][week][category]['incomes']
            if incomes > 0:
                home_lat, home_lon = get_lon_lat(home_zipcode)
                shop_lat, shop_lon = get_lon_lat(shop_zipcode)
                distance = haversine(home_lon, home_lat, shop_lon, shop_lat)
                if distance > min_km:
                    num_payments= home_info[key]['per_week'][week][category]['num_payments']
                    G.add_edge( home_zipcode, 
                               shop_zipcode, 
                               weight=incomes, 
                               incomes=incomes, 
                               num_payments=num_payments)
                           
    show_info(G)
    return G
                
     
    
def update_location_data(G, path):    
    for node in G.nodes():
        result = zipcodes.get(node)
        if result is not None:
            lat, lon = result
            G.node[node]['lat'] = float(lat)
            G.node[node]['lon'] = float(lon)
        else:
            G.node[node]['lat'] = 47.66
            G.node[node]['lon'] = -1.58
        
    return G
    
def analyze_graph(G):    
    
    #centralities and node metrics
    out_degrees = G.out_degree()
    in_degrees = G.in_degree()
    betweenness = nx.betweenness_centrality(G)
    eigenvector = nx.eigenvector_centrality_numpy(G)
    closeness = nx.closeness_centrality(G)
    pagerank = nx.pagerank(G)
    avg_neighbour_degree = nx.average_neighbor_degree(G)
    redundancy = bipartite.node_redundancy(G)
    load = nx.load_centrality(G)
    hits = nx.hits(G)
    vitality = nx.closeness_vitality(G)
    
    for name in G.nodes():
        G.node[name]['out_degree'] = out_degrees[name]
        G.node[name]['in_degree'] = in_degrees[name]
        G.node[name]['betweenness'] = betweenness[name]
        G.node[name]['eigenvector'] = eigenvector[name]
        G.node[name]['closeness'] = closeness[name]
        G.node[name]['pagerank'] = pagerank[name]
        G.node[name]['avg-neigh-degree'] = avg_neighbour_degree[name]
        G.node[name]['redundancy'] = redundancy[name]
        G.node[name]['load'] = load[name]
        G.node[name]['hits'] = hits[name]
        G.node[name]['vitality'] = vitality[name]
        
    #communities
    partitions = community.best_partition(G)
    for member, c in partitions.items():
        G.node[member]['community'] = c   
    
    return G
 
# ALL RELATIONS   
G = get_total_relations() 
G = update_location_data(G, './data/all_zipcodes.json')
# G = analyze_graph(G)
export_gexf(G, './data/processed_graph/directed.gexf')  

#BY WEEK AND CATEGORY
#G = get_relations_by_category('total','es_auto')
#G = update_location_data(G, './data/all_zipcodes.json')
#G = analyze_graph(G)
#export_gexf(G, './data/processed_graph/directed_es_auto_total.gexf')  

##MAXIMUN DISTANCE
#G = get_total_relations(99)
#G = update_location_data(G, './data/all_zipcodes.json')
#export_gexf(G, './data/processed_graph/directed_es_100km.gexf') 

   
print 'fin' 
