__author__ = 'zplin'
import sys
import json
import csv
from os import path
import numpy as np
from networkx import Graph, transitivity, clustering, average_shortest_path_length, connected_component_subgraphs
from networkx.readwrite import json_graph


if __name__ == '__main__':
    with open(sys.argv[1]) as g_file:
        data = json.load(g_file)
        g = Graph(json_graph.node_link_graph(data))
    print('Number of nodes:', g.number_of_nodes())
    print('Average degree:', 2 * g.number_of_edges()/g.number_of_nodes())
    print('Transitivity:', transitivity(g))
    cc = clustering(g)
    print('Average clustering coefficient:', np.mean(list(cc.values())))
    for subgraph in connected_component_subgraphs(g):
        if subgraph.number_of_nodes() > 1:
            print('Average shortest path length for subgraph of', subgraph.number_of_nodes(), ':',
                  average_shortest_path_length(subgraph))
    # Calculating average clustering coefficient for different degrees
    degree_cc = {}
    for node, degree in g.degree_iter():
        if degree not in degree_cc:
            degree_cc[degree] = []
        degree_cc[degree].append(cc[node])

    with open(path.join(path.dirname(sys.argv[1]), 'clustering.csv'), 'w', newline='') as cc_file:
        writer = csv.DictWriter(cc_file, ['degree', 'average_cc'])
        writer.writeheader()
        for degree in degree_cc:
            writer.writerow({'degree': degree, 'average_cc': np.mean(degree_cc[degree])})