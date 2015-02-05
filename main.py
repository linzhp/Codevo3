from codevo import Evolver, JavaPrinter
import csv
import os
import sys

if __name__ == '__main__':
    if os.path.exists('output'):
        for root, dirs, files in os.walk('output'):
            for name in files:
                os.remove(os.path.join(root, name))
    os.makedirs('output/src', exist_ok=True)
    evolver = Evolver()
    with open('output/steps.csv', 'w') as steps_file:
        writer = csv.DictWriter(steps_file, ['min_fitness', 'change_size'])
        writer.writeheader()
        for i in range(int(sys.argv[1])):
            print('Step %d' % i)
            change_size = evolver.step()
            min_fitness = min([data['fitness'] for node, data in evolver.reference_graph.nodes_iter(True)])
            writer.writerow({'min_fitness': min_fitness, 'change_size': change_size})

    with open('output/references.csv', 'w') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, in_degree in evolver.reference_graph.in_degree_iter():
            writer.writerow({
                'method': method_name,
                'class': evolver.reference_graph.node[method_name]['class'].name,
                'ref_count': in_degree
            })

    with open('output/classes.csv', 'w') as sub_file:
        writer = csv.DictWriter(sub_file, ['class', 'subclasses', 'lines'])
        writer.writeheader()
        for class_name, in_degree in evolver.inheritance_graph.in_degree_iter():
            klass = evolver.inheritance_graph.node[class_name]['class']
            java_printer = JavaPrinter()
            klass.accept(java_printer)
            writer.writerow({'class': class_name,
                             'subclasses': in_degree,
                             'lines': java_printer.result.count('\n') + 1})
            with open(os.path.join('output/src', class_name + '.java'), 'w') as java_file:
                java_file.write(java_printer.result)