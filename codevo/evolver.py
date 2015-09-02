from plyj.model import MethodDeclaration, MethodInvocation
from plyj.parser import Parser
from random import random
from codevo.utils import sample
from codevo.code_modifier import CodeModifier
from os import path
from networkx import DiGraph, Graph
import logging


class Evolver:
    def __init__(self, initial_classes=None):
        """
        :param initial_classes: assuming these classes has no method calls to or inheritances from each other
        :return: None
        """
        if initial_classes is None:
            with open(path.join(path.dirname(__file__), '..', 'App.java')) as java_file:
                parser = Parser()
                tree = parser.parse_file(java_file)
                initial_classes = tree.type_declarations
        self.p_create_class = 0.1
        self.p_no_inherit = 0.2
        self.code_modifier = CodeModifier()
        self.inheritance_graph = DiGraph()
        self.reference_graph = DiGraph()

        for c in initial_classes:
            self.inheritance_graph.add_node(c.name, {'class': c})
            for m in c.body:
                if isinstance(m, MethodDeclaration):
                    self.reference_graph.add_node(m.name,
                                                  {'method': m,
                                                   'class': c,
                                                   'fitness': random()
                                                   })

    def step(self):
        p_create_method = 0.1
        p_call_method = 0.14
        p_delete_method = 0.01
        p_update_method = 0.75
        change_size = 0
        while change_size == 0:
            action = sample([
                (self.create_method, p_create_method),
                (self.call_method, p_call_method),
                (self.update_method, p_update_method),
                (self.delete_method, p_delete_method)
            ])
            change_size = action()
            if self.reference_graph.number_of_nodes() == 0:
                logging.error(str(action) + ' has deleted all methods')
        logging.info('number of methods: %d' % self.reference_graph.number_of_nodes())
        return change_size

    def build_class_association(self):
        asso_graph = Graph()
        for e in self.reference_graph.edges_iter():
            asso_graph.add_edge(
                self.reference_graph.node[e[0]]['class'].name,
                self.reference_graph.node[e[1]]['class'].name)
        for e in self.inheritance_graph.edges_iter():
            asso_graph.add_edge(*e)
        return asso_graph

    def create_method(self):
        logging.info('creating a method')
        klass = None
        if random() < self.p_create_class:
            klass = self.create_class()
        else:
            classes = [(data['class'], len(data['class'].body) + 1)
                       for node, data in self.inheritance_graph.nodes_iter(data=True)]
            klass = sample(classes)
        method = self.code_modifier.create_method(klass)
        self.reference_graph.add_node(method.name,
                                      {'method': method,
                                       'class': klass
                                       }
                                      )
        # make a call from the new method
        self.call_method(method.name)
        # call the new method
        caller_name = self.choose_unfit_method()
        self.call_method(caller_name, method.name)
        return 3

    def call_method(self, caller_name=None, callee_name=None):
        logging.info('calling a method')
        caller_info = self.reference_graph.node[caller_name] if caller_name \
            else sample([(data, len(data['method'].body) + 1) for data in self.reference_graph.node.values()])
        callee_info = self.reference_graph.node[callee_name or self.choose_callee()]
        self.code_modifier.add_method_call(
            caller_info['method'], callee_info['method'], callee_info['class'])
        caller_info['fitness'] = random()
        self.reference_graph.add_edge(caller_info['method'].name, callee_info['method'].name)
        return 1

    def update_method(self):
        logging.info('updating a method')
        method_name = self.choose_unfit_method()
        method_info = self.reference_graph.node[method_name]
        # The method can be empty because it is the only remaining method
        if len(method_info['method'].body) == 0 or random() < 0.67:
            self.code_modifier.add_statement(method_info['method'])
        else:
            deleted_stmt = self.code_modifier.delete_statement(method_info['method'])
            if isinstance(deleted_stmt, MethodInvocation):
                # check if there is any remaining references
                remaining_method_calls = False
                for stmt in method_info['method'].body:
                    if isinstance(stmt, MethodInvocation) and stmt.name == deleted_stmt.name:
                        remaining_method_calls = True
                        break
                if not remaining_method_calls:
                    self.reference_graph.remove_edge(method_name, deleted_stmt.name)
        if len(method_info['method'].body) == 0:
            return self.delete_method(method_name) + 1
        else:
            method_info['fitness'] = random()
            return 1

    def delete_method(self, method_name=None):
        """
        Delete a method and delete the method call from its callers. It a caller becomes
        empty after deleting the method, delete the caller as well and the deletion propagates
        :param method_name: The method to be deleted. If None, randomly choose one
        :return: The number of changes made
        """
        logging.info('deleting a method')
        change_size = 0
        if self.reference_graph.number_of_nodes() == 1:
            # Don't delete the last method
            return 0
        if method_name is None:
            # method = choice(self.reference_graph.nodes())
            method_name = self.choose_unfit_method()
        method_info = self.reference_graph.node[method_name]
        klass = method_info['class']
        void_callers = []
        for caller_name in self.reference_graph.predecessors_iter(method_name):
            if caller_name != method_name:
                caller_info = self.reference_graph.node[caller_name]
                caller = caller_info['method']
                self.code_modifier.delete_method_call(caller, method_info['method'], klass)
                change_size += 1
                if len(caller.body) == 0:
                    void_callers.append(caller_name)
                else:
                    caller_info['fitness'] = random()

        self.code_modifier.delete_method(klass, method_info['method'])
        change_size += len(method_info['method'].body)
        self.reference_graph.remove_node(method_name)
        change_size += 1
        # recursively remove all empty callers
        for caller_name in void_callers:
            change_size += self.delete_method(caller_name)
        if len(klass.body) == 0:
            # remove the class and update all its subclasses
            for class_name in self.inheritance_graph.predecessors_iter(klass.name):
                c = self.inheritance_graph.node[class_name]['class']
                c.extends = None
                change_size += 1
            self.inheritance_graph.remove_node(klass.name)
            change_size += 1
        return change_size

    def create_class(self):
        superclass_name = None
        if random() > self.p_no_inherit:
            class_info = [(node, in_degree + 1) for node, in_degree in self.inheritance_graph.in_degree_iter()]
            superclass_name = sample(class_info)
        klass = self.code_modifier.create_class(superclass_name)
        self.inheritance_graph.add_node(klass.name, {'class': klass})
        if superclass_name:
            self.inheritance_graph.add_edge(klass.name, superclass_name)
        return klass

    def choose_unfit_method(self):
        """
        :return: the method with least fitness number. Can change to a probabilistic function that biases towards
        less fit methods if the current implementation makes the system too stable
        """
        min_fitness = 1
        unfit_method = None
        for method, data in self.reference_graph.nodes_iter(True):
            if data['fitness'] < min_fitness:
                min_fitness = data['fitness']
                unfit_method = method
        return unfit_method

    def choose_callee(self):
        return sample([(method_name, len(self.reference_graph.pred[method_name]) + 1)
                       for method_name in self.reference_graph.node])

