# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 09:14:17 2013

@author: aitor
"""

import networkx as nx
from networkx.readwrite import gexf
from networkx.readwrite import json_graph
import json
from networkx.algorithms import bipartite
import community
import json

from bbvalib import create_mongoclient
from geo_tools import haversine

categories = ['es_auto','es_barsandrestaurants','es_contents','es_fashion',
              'es_food','es_health','es_home','es_hotelservices','es_hyper',
              'es_leisure','es_otherservices','es_propertyservices',
              'es_sportsandtoys','es_tech','es_transportation','es_travel',
              'es_wellnessandbeauty']

json_data=open('./data/all_zipcodes.json')
zipcodes = json.load(json_data)
json_data.close() 

def show_info(G):
    print 'Is directed?: %s' %(str(G.is_directed())) 
    print 'Nodes: %i' % (len(G.nodes()))
    print 'Edges: %i' % (len(G.edges()))
    
def export_gexf(G, path):
    gexf.write_gexf(G, path)    

def export_json(G, path):
    jsonString= json_graph.dumps(G)
    jsonData = json.loads(jsonString)
    nodes = jsonData['nodes']
    print nodes
    links = jsonData['links']
    
    res = {}
    res['nodes'] = nodes
    res['links'] = links
    jsonString = json.dumps(res)
    jsonString = jsonString.replace('id', 'name')
    jsonString = jsonString.replace('weight', 'value')
    print jsonString
    with open(path, 'w') as f:
     f.write(jsonString)
     f.flush()

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
    
def get_total_relations(min_km = -1):    
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
    
def get_relations_by_category(week, category, min_km = -1):
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

# most_central: the node with the highest eigenvector centrality. The 'most important'
# zipcode in the network
# biggest_traveler: the node with the biggest outdegree. The zipcode that have has 
# most transaction in other zipcodes
# biggest_receiver: the node with the biggest indegree. The zipcode that has received
# most transactions from other zipcodes
# biggest_expender: the origin node of the edge with the highest weight. The originating
# zipcode for the biggest transaction.
# biggest_earner: the destination node of the edge with the highest weight. The destination
# zipcode for the biggest transaction.

def create_summary(G):
    out_degrees = G.out_degree()
    in_degrees = G.in_degree()
    eigenvector = nx.eigenvector_centrality_numpy(G)
    
    most_central, _ = get_biggest(eigenvector)
    biggest_traveler, _ = get_biggest(out_degrees)
    biggest_receiver, _ = get_biggest(in_degrees)
    
    biggest_weight = 0
    biggest_expender = ''
    biggest_earner = ''
    for edge in G.edges():
        if biggest_weight < G.edge[edge[0]][edge[1]]['weight']:
            biggest_weight = G.edge[edge[0]][edge[1]]['weight']
            biggest_expender = edge[0]
            biggest_earner = edge[1]
            
    summary = {}
    summary['most_central'] = most_central
    summary['biggest_traveler'] = biggest_traveler
    summary['biggest_receiver'] = biggest_receiver
    summary['biggest_expender'] = biggest_expender
    summary['biggest_earner'] = biggest_earner
            
    return summary
        
    
    
    
def get_biggest(d):
    biggest_value = 0
    biggest = ''
    for pair in d.items():
        if biggest_value < pair[1]:
            biggest_value = pair[1]
            biggest = pair[0]
            
    return biggest, biggest_value
    
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
    
def get_groups(G):
    partitions = community.best_partition(G.to_undirected())
    for member, c in partitions.items():
        G.node[member]['group'] = c
    return G
    
def create_complete_summary():
    summary = {}
    print 'Getting total summary'
    G = get_total_relations() 
    G = update_location_data(G, './data/all_zipcodes.json')
    export_gexf(G, './data/processed_graph/all-relations-directed.gexf')
    complete_summary = create_summary(G)
    summary['complete'] = complete_summary
    
    for c in categories:
        print 'Getting ' + c + ' summary'
        G = get_relations_by_category('total', c)
        G = update_location_data(G, './data/all_zipcodes_.json')
        export_gexf(G, './data/processed_graph/' + c + '-directed.gexf')
        cat_summary = create_summary(G)
        summary[c] = cat_summary
    
    return summary


# CREATE SUMMARY  
#summ = create_complete_summary();
#print summ 
 
 
# ALL RELATIONS   
#G = get_total_relations() 
#G = update_location_data(G, './data/all_zipcodes.json')
#G = analyze_graph(G)
#export_gexf(G, './data/processed_graph/all-relations.gexf')  

#BY WEEK, CATEGORY AND MINIMUN DISTANCE
#G = get_relations_by_category('total','es_auto', 99)
#G = update_location_data(G, './data/all_zipcodes.json')
##G = analyze_graph(G)
#export_gexf(G, './data/processed_graph/directed_es_auto_total_100km.gexf')  

##MAXIMUN DISTANCE
#G = get_total_relations(1000)

#JSON
print 'starting'
G = get_relations_by_category('total','es_auto', 10)
G = get_groups(G)
export_json(G, './sketches/aitor/300km.json') 

   
print 'fin' 