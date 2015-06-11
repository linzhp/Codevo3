from os import path
from random import random
from networkx import DiGraph
from math import floor

from plyj.model import *
from plyj.parser import Parser

from codevo.utils import sample


class CodeModifier:
    def __init__(self):
        self.counter = 0
        with open(path.join(path.dirname(__file__), '..', 'App.java')) as java_file:
            parser = Parser()
            tree = parser.parse_file(java_file)
            initial_classes = tree.type_declarations
        self.inheritance_graph = DiGraph()
        self.reference_graph = DiGraph()

        for c in initial_classes:
            self.inheritance_graph.add_node(c.name, {'class': c})
            for m in c.body:
                if isinstance(m, MethodDeclaration):
                    self.reference_graph.add_node(m.name,
                                                  {'method': m,
                                                   'class_name': c.name,
                                                   'fitness': random()
                                                   })

    def get_class_name(self, method_name):
        return self.reference_graph.node[method_name]['class_name']

    def choose_random_method(self):
        """
        Choose a random method, weighted by its size
        :return: the method name
        """
        return sample([(method_name, len(data['method'].body) + 1)
                       for method_name, data in self.reference_graph.nodes_iter(True)])

    def choose_random_class(self):
        """
        Choose a random class, weighted by its size
        :return: the class name
        """
        return sample([(class_name, len(data['class'].body) + 1)
                       for class_name, data in self.inheritance_graph.nodes_iter(data=True)])

    def choose_random_neighbor(self, method_name):
        neighbors = self.reference_graph.neighbors(method_name)
        num_neighbors = len(neighbors)
        if num_neighbors > 0:
            return neighbors[floor(random() * num_neighbors)]
        else:
            return None

    def assign_new_fitness(self, method_name):
        self.reference_graph.node[method_name]['fitness'] = random()

    def create_method(self, class_name):
        """
        The created methods are static methods for now
        """
        klass = self.inheritance_graph[class_name]['class']
        method = MethodDeclaration(
            'method' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        klass.body.append(method)
        method_info = {'method': method, 'class_name': class_name, 'fitness': random()}
        self.reference_graph.add_node(method.name, method_info)
        return method

    def delete_method(self, class_node, method):
        class_node.body.remove(method)

    def create_class(self, superclass_name):
        klass = ClassDeclaration('Class' + str(self.counter), [])
        if superclass_name:
            klass.extends = Type(Name(superclass_name))
        self.counter += 1
        self.inheritance_graph.add_node(klass.name, {'class': klass})
        if superclass_name:
            self.inheritance_graph.add_edge(klass.name, superclass_name)
        return klass

    def add_method_call(self, caller_name, callee_name):
        target_name = self.reference_graph[callee_name]['class_name']
        ref = MethodInvocation(callee_name, target=Name(target_name))
        caller = self.reference_graph[caller_name]['method']
        caller.body.append(ExpressionStatement(ref))
        self.reference_graph.add_edge(caller_name, callee_name)
        return ref

    def delete_method_call(self, from_method, to_method, target):
        to_delete = [stmt for stmt in from_method.body
                     if isinstance(stmt, ExpressionStatement) and
                        isinstance(stmt.expression, MethodInvocation) and
                        stmt.expression.name == to_method.name and
                        stmt.expression.target.value == target.name]
        for stmt in to_delete:
            from_method.body.remove(stmt)

    def add_statement(self, method_name):
        method = self.reference_graph[method_name]['method']
        stmt = self.create_statement()
        method.body.append(stmt)

    def delete_statement(self, method):
        return method.body.pop()

    def create_statement(self):
        """
        Generate a statement. May use a fuzzer to generate a variety of statements
        :return:
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