from codevo import Evolver, JavaPrinter
import csv
import os

if __name__ == '__main__':
    if os.path.exists('output'):
        for root, dirs, files in os.walk('output'):
            for name in files:
                os.remove(os.path.join(root, name))
    else:
        os.makedirs('output')
    evolver = Evolver()
    with open('output/fitness.txt', 'w') as fit_file, open('output/change_size.txt', 'w') as size_file:
        for i in range(100000):
            print('Step %d' % i)
            size_file.write('%d\n' % evolver.step())
            fitness = [str(data['fitness']) for node, data in evolver.reference_graph.nodes_iter(True)]
            fit_file.write(','.join(fitness) + '\n')

    with open('output/references.csv', 'w') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, in_degree in evolver.reference_graph.in_degree_iter():
            writer.writerow({
                'method': method_name,
                'class': evolver.reference_graph.node[method_name]['class'].name,
                'ref_count': in_degree
            })

    with open('output/subclasses.csv', 'w') as sub_file:
        writer = csv.DictWriter(sub_file, ['class', 'subclasses'])
        writer.writeheader()
        for class_name, in_degree in evolver.inheritance_graph.in_degree_iter():
            writer.writerow({'class': class_name, 'subclasses': in_degree})
            klass = evolver.inheritance_graph.node[class_name]['class']
            java_printer = JavaPrinter()
            klass.accept(java_printer)
            with open('output/src' + class_name + '.java', 'w') as java_file:
                java_file.write(java_printer.result)