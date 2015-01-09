from codevo import Evolver
import csv

if __name__ == '__main__':
    evolver = Evolver()
    for i in range(1000):
        evolver.step()

    with open('references.csv', 'w') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, data in evolver.reference_graph.nodes_iter(True):
            writer.writerow({
                'method': method_name,
                'class': data['class'].name,
                'ref_count': evolver.reference_graph.in_degree(method_name)
            })