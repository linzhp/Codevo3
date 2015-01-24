from codevo import Evolver
import csv

if __name__ == '__main__':
    evolver = Evolver()
    with open('fitness.txt', 'w') as fit_file, open('change_size.txt', 'w') as size_file:
        for i in range(50000):
            print('Step %d' % i)
            size_file.write('%d\n' % evolver.step())
            fitness = [str(data['fitness']) for node, data in evolver.reference_graph.nodes_iter(True)]
            fit_file.write(','.join(fitness) + '\n')

    with open('references.csv', 'w') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, in_degree in evolver.reference_graph.in_degree_iter():
            writer.writerow({
                'method': method_name,
                'class': evolver.reference_graph.node[method_name]['class'].name,
                'ref_count': in_degree
            })
