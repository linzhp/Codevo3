from os import path
from random import random
from networkx import Graph, DiGraph, relabel_nodes
from networkx.readwrite import json_graph
import json
from math import floor
from heapq import nsmallest
import csv

from plyj.model import *
from plyj.parser import Parser

from codevo.utils import sample
from codevo.java_printer import JavaPrinter


class Codebase:
    def __init__(self):
        self.counter = 0
        self._revisions = []
        with open(path.join(path.dirname(__file__), '..', 'App.java')) as java_file:
            parser = Parser()
            tree = parser.parse_file(java_file)
            initial_classes = tree.type_declarations
        self._inheritance_graph = DiGraph()
        self._method_call_graph = DiGraph()

        for c in initial_classes:
            self._inheritance_graph.add_node(c.name, {'class': c})
            for m in c.body:
                if isinstance(m, MethodDeclaration):
                    self._method_call_graph.add_node(m.name,
                                                  {'method': m,
                                                   'class_name': c.name,
                                                   'fitness': random()
                                                   })

    def get_class_name(self, method_name):
        return self._method_call_graph.node[method_name]['class_name']

    def size_of(self, method_name):
        return len(self._method_call_graph.node[method_name]['method'].body)

    def number_of_methods(self):
        return len(self._method_call_graph)

    def number_of_classes(self):
        return len(self._inheritance_graph)

    def has_method(self, method_name):
        return self._method_call_graph.has_node(method_name)

    def choose_random_method(self):
        """
        Choose a random method, weighted by its size
        :return: the method name
        """
        return sample([(method_name, len(data['method'].body) + 1)
                       for method_name, data in self._method_call_graph.nodes_iter(True)])

    def choose_random_class(self):
        """
        Choose a random class, weighted by its size
        :return: the class name
        """
        return sample([(class_name, len(data['class'].body) + 1)
                       for class_name, data in self._inheritance_graph.nodes_iter(data=True)])

    def least_fit_methods(self, n=1):
        """
        :return: the name of the method with smallest fitness value
        """
        return nsmallest(n, self._method_call_graph,
                         key=lambda method_name: self._method_call_graph.node[method_name]['fitness'])

    def choose_random_neighbor(self, method_name):
        neighbors = self._method_call_graph.neighbors(method_name)
        num_neighbors = len(neighbors)
        if num_neighbors > 0:
            return neighbors[floor(random() * num_neighbors)]
        else:
            return None

    def caller_names(self, method_name):
        """
        :param method_name:
        :return: caller method names iterator
        """
        return self._method_call_graph.predecessors_iter(method_name)

    def method_invocations(self, method_name):
        """
        Generator for MethodInvocation instances of method_name
        :param method_name:
        :return:
        """
        for caller_name in self._method_call_graph.predecessors_iter(method_name):
            caller = self._method_call_graph.node[caller_name]['method']
            for stmt in caller.body:
                if Codebase.is_invocation(stmt, method_name):
                    yield stmt.expression

    def create_method(self, class_name):
        """
        The created methods are static methods for now
        """
        klass = self._inheritance_graph.node[class_name]['class']
        method = MethodDeclaration(
            'method' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        klass.body.append(method)
        method_info = {'method': method, 'class_name': class_name, 'fitness': random()}
        self._method_call_graph.add_node(method.name, method_info)
        return 1, method.name

    def delete_method(self, method_name):
        """
        Delete the method and update callers
        :param method_name:
        :return:
        """
        # remove method invocation
        change_size = 1
        for caller_name in self._method_call_graph.predecessors_iter(method_name):
            caller_info = self._method_call_graph.node[caller_name]
            caller = caller_info['method']
            old_size = len(caller.body)
            caller.body = [stmt for stmt in caller.body
                           if not Codebase.is_invocation(stmt, method_name)
                           ]
            change_size += old_size - len(caller.body)
            caller_info['fitness'] = random()
        method_info = self._method_call_graph.node[method_name]
        method = method_info['method']
        class_name = method_info['class_name']
        klass = self._inheritance_graph.node[class_name]['class']
        klass.body.remove(method)
        self._method_call_graph.remove_node(method_name)
        if len(klass.body) == 0:
            # remove inheritance from all subclasses
            for subclass_name in self._inheritance_graph.predecessors_iter(class_name):
                subclass = self._inheritance_graph.node[subclass_name]['class']
                subclass.extends = None
                change_size += 1
            self._inheritance_graph.remove_node(class_name)
            change_size += 1
        return change_size

    def create_class(self, superclass_name):
        klass = ClassDeclaration('Class' + str(self.counter), [])
        if superclass_name:
            klass.extends = Type(Name(superclass_name))
        self.counter += 1
        self._inheritance_graph.add_node(klass.name, {'class': klass})
        if superclass_name:
            self._inheritance_graph.add_edge(klass.name, superclass_name)
        return 1, klass.name

    def add_method_call(self, caller_name, callee_name):
        callee_info = self._method_call_graph.node[callee_name]
        caller_info = self._method_call_graph.node[caller_name]
        caller = caller_info['method']
        num_params = len(callee_info['method'].parameters)
        # trying to find enough variables for the method arguments
        arguments = []
        for p in caller.parameters:
            if len(arguments) >= num_params:
                break
            else:
                arguments.append(Name(p.variable.name))
        for s in caller.body:
            if len(arguments) >= num_params:
                break
            if isinstance(s, VariableDeclaration):
                for vd in s.variable_declarators:
                    arguments.append(Name(vd.variable.name))
        while len(arguments) < num_params:
            arguments.append(Literal(self.counter))
        target_name = callee_info['class_name']
        ref = MethodInvocation(callee_name, arguments, target=Name(target_name))
        caller.body.append(ExpressionStatement(ref))
        self._method_call_graph.add_edge(caller_name, callee_name)
        caller_info['fitness'] = random()
        return 1

    def add_statement(self, method_name):
        method_info = self._method_call_graph.node[method_name]
        method = method_info['method']
        stmt = self.create_variable_declaration()
        method.body.append(stmt)
        method_info['fitness'] = random()
        return 1

    def add_parameter(self, method_name):
        """
        Add a parameter to the method, and update all its callers
        :param method_name:
        :return:
        """
        method_info = self._method_call_graph.node[method_name]
        method = method_info['method']
        parameters = method.parameters
        parameters.append(FormalParameter(Variable('param%d' % len(parameters)), Type(Name('int'))))
        change_size = 1
        for caller_name in self._method_call_graph.predecessors_iter(method_name):
            caller_info = self._method_call_graph.node[caller_name]
            caller = caller_info['method']
            local_variables = [p.variable.name for p in caller.parameters]
            for s in caller.body:
                if isinstance(s, VariableDeclaration):
                    for vd in s.variable_declarators:
                        local_variables.append(vd.variable.name)
                elif Codebase.is_invocation(s, method_name):
                    if len(local_variables) > 0:
                        s.expression.arguments.append(Name(local_variables[-1]))
                    else:
                        s.expression.arguments.append(Literal(self.counter))
                change_size += 1
            caller_info['fitness'] = random()
        return change_size

    def move_method(self, method_name, to_class_name):
        method_info = self._method_call_graph.node[method_name]
        from_class_name = method_info['class_name']
        if from_class_name == to_class_name:
            return 0
        method = method_info['method']
        from_class_body = self._inheritance_graph.node[from_class_name]['class'].body
        from_class_body.remove(method)
        to_class_body = self._inheritance_graph.node[to_class_name]['class'].body
        to_class_body.append(method)
        method_info['class_name'] = to_class_name
        change_size = 1
        # update references
        for method_invocation in self.method_invocations(method_name):
            method_invocation.target = Name(to_class_name)
            change_size += 1
        return change_size

    def rename_method(self, method_name):
        new_name = 'method%d' % self.counter
        self.counter += 1
        method_info = self._method_call_graph.node[method_name]
        method_info['method'].name = new_name
        change_size = 1
        for inv in self.method_invocations(method_name):
            inv.name = new_name
            change_size += 1
        relabel_nodes(self._method_call_graph, {method_name: new_name}, copy=False)
        method_info['fitness'] = random()
        return change_size, new_name

    def create_variable_declaration(self):
        """
        :return: the new variable declaration
        """
        var = VariableDeclaration(
            type='int',
            variable_declarators=[VariableDeclarator(
                variable=Variable(
                    name='var' + str(self.counter)
                ),
                initializer=Literal(self.counter)
            )]
        )
        self.counter += 1
        return var

    def save(self, output_dir):
        with open(path.join(output_dir, 'commits.csv'), 'w', newline='') as commits_file:
            writer = csv.DictWriter(commits_file, ['min_fitness', 'change_size'])
            writer.writeheader()
            writer.writerows(self._revisions)

        with open(path.join(output_dir, 'classes.csv'), 'w', newline='') as classes_file:
            writer = csv.DictWriter(classes_file, ['class', 'subclasses', 'lines'])
            writer.writeheader()
            for class_name, in_degree in self._inheritance_graph.in_degree_iter():
                klass = self._inheritance_graph.node[class_name]['class']
                java_printer = JavaPrinter()
                klass.accept(java_printer)
                writer.writerow({'class': class_name,
                                 'subclasses': in_degree,
                                 'lines': java_printer.result.count('\n') + 1})
                with open(path.join(output_dir, 'src', class_name + '.java'), 'w') as java_file:
                    java_file.write(java_printer.result)

        with open(path.join(output_dir, 'methods.csv'), 'w', newline='') as methods_file:
            writer = csv.DictWriter(methods_file, ['method', 'class', 'ref_count'])
            writer.writeheader()
            for method_name, in_degree in self._method_call_graph.in_degree_iter():
                writer.writerow({
                    'method': method_name,
                    'class': self._method_call_graph.node[method_name]['class_name'],
                    'ref_count': in_degree
                })

        with open(path.join(output_dir, 'methods.json'), 'w') as methods_file:
            data = json_graph.node_link_data(self._method_call_graph)
            json.dump(data, methods_file, skipkeys=True, default=lambda d: None)

        association_graph = Graph()
        for e in self._method_call_graph.edges_iter():
            association_graph.add_edge(
                self._method_call_graph.node[e[0]]['class_name'],
                self._method_call_graph.node[e[1]]['class_name'])
        for e in self._inheritance_graph.edges_iter():
            association_graph.add_edge(*e)
        with open(path.join(output_dir, 'classes.json'), 'w') as classes_file:
            data = json_graph.node_link_data(association_graph)
            json.dump(data, classes_file, skipkeys=True)

    def commit(self, change_size):
        self._revisions.append({
            'min_fitness': min(self._method_call_graph.node[method_name]['fitness']
                               for method_name in self._method_call_graph),
            'change_size': change_size
        })

    @staticmethod
    def is_invocation(stmt, method_name):
        return isinstance(stmt, ExpressionStatement) and \
               isinstance(stmt.expression, MethodInvocation) and \
               stmt.expression.name == method_name

