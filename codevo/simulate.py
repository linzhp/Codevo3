from codevo import Evolver, JavaPrinter
import csv
import os
import sys
import logging
from networkx.readwrite import json_graph
import json
import random
from time import time
from argparse import ArgumentParser

if __name__ == '__main__':
    arg_parser = ArgumentParser(description='Run the simulation')
    arg_parser.add_argument('-o', dest='output_dir', type=str, default='output', help='output directory')
    arg_parser.add_argument('num_steps', metavar='N', type=int, help='number of steps')
    arg_parser.add_argument('-s', dest='save_source', action='store_true',
                            help='whether to save the Java source code')
    options = arg_parser.parse_args(sys.argv[1:])
    if os.path.exists(options.output_dir):
        for root, dirs, files in os.walk(options.output_dir):
            for name in files:
                os.remove(os.path.join(root, name))
    else:
        os.makedirs(options.output_dir)
    if options.save_source:
        os.makedirs(os.path.join(options.output_dir, 'src'), exist_ok=True)
    random_seed = round(time())
    print('Using seed', random_seed)
    random.seed(random_seed)
    evolver = Evolver()
    with open(os.path.join(options.output_dir, 'steps.csv'), 'w', newline='') as steps_file:
        writer = csv.DictWriter(steps_file, ['min_fitness', 'change_size'])
        writer.writeheader()
        for i in range(options.num_steps):
            logging.info('Step %d' % i)
            change_size = evolver.step()
            min_fitness = min([data['fitness'] for data in evolver.reference_graph.node.values()])
            writer.writerow({'min_fitness': min_fitness, 'change_size': change_size})

    with open(os.path.join(options.output_dir, 'references.csv'), 'w', newline='') as ref_file:
        writer = csv.DictWriter(ref_file, ['method', 'class', 'ref_count'])
        writer.writeheader()
        for method_name, in_degree in evolver.reference_graph.in_degree_iter():
            writer.writerow({
                'method': method_name,
                'class': evolver.reference_graph.node[method_name]['class'].name,
                'ref_count': in_degree
            })
    collab_graph = evolver.build_class_association()
    with open(os.path.join(options.output_dir, 'classes.csv'), 'w', newline='') as sub_file:
        writer = csv.DictWriter(sub_file, ['class', 'subclasses', 'lines', 'degree'])
        writer.writeheader()
        for class_name, in_degree in evolver.inheritance_graph.in_degree_iter():
            klass = evolver.inheritance_graph.node[class_name]['class']
            java_printer = JavaPrinter()
            klass.accept(java_printer)
            writer.writerow({'class': class_name,
                             'subclasses': in_degree,
                             'lines': java_printer.result.count('\n') + 1,
                             'degree': collab_graph.degree(class_name) if class_name in collab_graph else 0
                             })
            if options.save_source:
                with open(os.path.join('output/src', class_name + '.java'), 'w') as java_file:
                    java_file.write(java_printer.result)

    with open(os.path.join(options.output_dir, 'references.json'), 'w') as ref_file:
        data = json_graph.node_link_data(evolver.reference_graph)
        json.dump(data, ref_file, skipkeys=True, default=lambda d: None)

    with open(os.path.join(options.output_dir, 'associations.json'), 'w') as asso_file:
        data = json_graph.node_link_data(collab_graph)
        json.dump(data, asso_file, skipkeys=True)