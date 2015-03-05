__author__ = 'zplin'
import sys
import json
import csv
import numpy as np
from networkx import Graph, transitivity, clustering
from networkx.readwrite import json_graph


if __name__ == '__main__':
    with open(sys.argv[1]) as g_file:
        data = json.load(g_file)
        g = Graph(json_graph.node_link_graph(data))
    print('Number of nodes:', g.number_of_nodes())
    print('Average degrees:', 2 * g.number_of_edges()/g.number_of_nodes())
    print('Transitivity:', transitivity(g))
    # Calculating average clustering coefficient for different degrees
    cc = clustering(g)
    degree_cc = {}
    for node, degree in g.degree_iter():
        if degree not in degree_cc:
            degree_cc[degree] = []
        degree_cc[degree].append(cc[node])

    with open('output/clustering.csv', 'w', newline='') as cc_file:
        writer = csv.DictWriter(cc_file, ['degree', 'average_cc'])
        writer.writeheader()
        for degree in degree_cc:
            writer.writerow({'degree': degree, 'average_cc': np.mean(degree_cc[degree])})