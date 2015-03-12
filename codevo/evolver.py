from plyj.model import MethodDeclaration, MethodInvocation
from plyj.parser import Parser
from random import random
from codevo.utils import sample
from codevo.code_modifier import CodeModifier
from os import path
from networkx import DiGraph
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
                                                   'fitness': random(),
                                                   'size': len(m.body)
                                                  })

    def step(self):
        p_create_method = 126214
        p_call_method = 175060
        p_delete_method = 0
        p_update_method = 889339
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
        callee_info = self.choose_callee()
        self.code_modifier.create_reference(method, callee_info['method'], callee_info['class'])
        self.reference_graph.add_node(method.name,
                                      {'method': method,
                                       'class': klass,
                                       'fitness': random(),
                                       'size': 1
                                      }
        )
        self.reference_graph.add_edge(method.name, callee_info['method'].name)
        caller_name = self.choose_unfit_method()
        caller_info = self.reference_graph.node[caller_name]
        self.code_modifier.create_reference(caller_info['method'], method, klass)
        caller_info['fitness'] = random()
        caller_info['size'] += 1
        self.reference_graph.add_edge(caller_name, method.name)
        return 3

    def call_method(self):
        logging.info('calling a method')
        caller_info = sample([(data, data['size'])
                              for data in self.reference_graph.node.values()])
        callee_info = self.choose_callee()
        self.code_modifier.create_reference(
            caller_info['method'], callee_info['method'], callee_info['class'])
        caller_info['fitness'] = random()
        caller_info['size'] += 1
        self.reference_graph.add_edge(caller_info['method'].name, callee_info['method'].name)
        return 1

    def update_method(self):
        logging.info('updating a method')
        method_name = self.choose_unfit_method()
        method_info = self.reference_graph.node[method_name]
        if random() < 0.67:
            self.code_modifier.add_statement(method_info['method'])
            method_info['size'] += 1
        else:
            deleted_stmt = self.code_modifier.delete_statement(method_info['method'])
            if isinstance(deleted_stmt, MethodInvocation):
                self.reference_graph.remove_edge(method_name, deleted_stmt.name)
            method_info['size'] -= 1
        if method_info['size'] == 0:
            return self.delete_method(method_name) + 1
        else:
            method_info['fitness'] = random()
            return 1

    def delete_method(self, method=None):
        """
        Delete a method and delete the method call from its callers. It a caller becomes
        empty after deleting the method, delete the caller as well and the deletion propagates
        :param method: The method to be deleted. If None, randomly choose one
        :return: The number of changes made
        """
        logging.info('deleting a method')
        change_size = 0
        if self.reference_graph.number_of_nodes() == 1:
            # Don't delete the last method
            return 0
        if method is None:
            # method = choice(self.reference_graph.nodes())
            method = self.choose_unfit_method()
        method_info = self.reference_graph.node[method]
        class_node = method_info['class']
        void_callers = []
        for caller in self.reference_graph.predecessors_iter(method):
            if caller != method:
                caller_info = self.reference_graph.node[caller]
                caller_node = caller_info['method']
                self.code_modifier.delete_reference(caller_node, method_info['method'], class_node)
                change_size += 1
                if len(caller_node.body) == 0:
                    void_callers.append(caller)
                else:
                    caller_info['size'] = len(caller_node.body)
                    caller_info['fitness'] = random()
        self.code_modifier.delete_method(class_node, method_info['method'])
        change_size += method_info['size']
        self.reference_graph.remove_node(method)
        if len(class_node.body) == 0:
            self.inheritance_graph.remove_node(class_node.name)
        # recursively remove all void callers
        for caller in void_callers:
            change_size += self.delete_method(caller)
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
        return sample([(self.reference_graph.node[method_name], len(self.reference_graph.pred[method_name]) + 1)
                       for method_name in self.reference_graph.node])

