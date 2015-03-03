__author__ = 'zplin'
import sys
import json
from networkx import Graph, transitivity
from networkx.readwrite import json_graph


if __name__ == '__main__':
    with open(sys.argv[1]) as g_file:
        data = json.load(g_file)
        g = Graph(json_graph.node_link_graph(data))
    print('Number of nodes:', g.number_of_nodes())
    print('Average degrees:', 2 * g.number_of_edges()/g.number_of_nodes())
    print('Transitivity:', transitivity(g))