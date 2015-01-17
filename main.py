from codevo import Evolver
import csv

if __name__ == '__main__':
    evolver = Evolver()
    for i in range(10000):
        evolver.step()

    with open('references.csv', 'w') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, in_degree in evolver.reference_graph.in_degree_iter():
            writer.writerow({
                'method': method_name,
                'class': evolver.reference_graph.node[method_name]['class'].name,
                'ref_count': in_degree
            })
