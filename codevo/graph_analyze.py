__author__ = 'zplin'

import sys
from pymongo import MongoClient
from networkx import Graph

def read_graph(rev):
    client = MongoClient()
    references = client.evolution.references
    doc = references.find_one({'_id': rev})
    g = Graph()
    del doc['_id']
    for v in doc:
        g.add_node(v)
        for neighbor in doc[v]:
            if neighbor in doc:
                g.add_edge(v, neighbor)
    return g



if __name__ == '__main__':
    g = read_graph(sys.argv[1])
    print('Number of Vertices:', g.number_of_nodes())
    print('Number of Edges:', g.number_of_edges())