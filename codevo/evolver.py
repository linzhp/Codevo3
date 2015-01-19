from plyj.model import MethodDeclaration
from plyj.parser import Parser
from random import random
from codevo.utils import sample
from codevo.code_modifier import CodeModifier
from os import path
from networkx import DiGraph


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
                    self.reference_graph.add_node(m.name, {'method': m, 'class': c, 'fitness': random()})

    def step(self):
        # Growth rate adapted from Turski (2002)
        num_of_refs = self.reference_graph.number_of_edges()
        p_create_method = 0.9 / (num_of_refs + 1)
        p_call_method = 1 - p_create_method
        p_delete_method = 0.1 / (num_of_refs + 1)
        p_update_method = 1 - p_delete_method
        action = sample([self.create_method, self.call_method, self.update_method, self.delete_method],
                        [p_create_method, p_call_method, p_update_method, p_delete_method])
        action()
        print('number of methods: %d' % self.reference_graph.number_of_nodes())

    def create_method(self):
        print('creating a method')
        klass = None
        if random() < self.p_create_class:
            klass = self.create_class()
        else:
            classes = []
            sizes = []
            for node, data in self.inheritance_graph.nodes_iter(data=True):
                classes.append(data['class'])
                sizes.append(len(data['class'].body))
            klass = sample(classes, [s + 1 for s in sizes])
        method = self.code_modifier.create_method(klass)
        self.reference_graph.add_node(method.name, {'method': method, 'class': klass, 'fitness': random()})
        return method

    def call_method(self):
        print('calling a method')
        methods = []
        sizes = []
        in_degrees = []
        for node, in_degree in self.reference_graph.in_degree_iter():
            in_degrees.append(in_degree)
            data = self.reference_graph.node[node]
            methods.append(data)
            sizes.append(len(data['method'].body))

        caller_info = sample(methods, [s + 1 for s in sizes])
        callee_info = sample(methods, [d + 1 for d in in_degrees])
        self.code_modifier.create_reference(
            caller_info['method'], callee_info['method'], callee_info['class'])
        # The will introduce some instability when the probability of creating and deleting methods drops to near 0
        caller_info['fitness'] = random()
        self.reference_graph.add_edge(caller_info['method'].name, callee_info['method'].name)

    def update_method(self):
        print('updating a method')
        method = self.choose_unfit_method()
        method_info = self.reference_graph.node[method]
        self.code_modifier.add_statement(method_info['method'])
        method_info['fitness'] = random()

    def delete_method(self, method=None):
        print('deleting a method')
        if self.reference_graph.number_of_nodes() == 1:
            # Don't delete the last method
            return
        if method is None:
            method = self.choose_unfit_method()
        method_info = self.reference_graph.node[method]
        class_node = method_info['class']
        void_callers = []
        for caller in self.reference_graph.predecessors_iter(method):
            if (caller != method):
                caller_info = self.reference_graph.node[caller]
                caller_node = caller_info['method']
                self.code_modifier.delete_reference(caller_node, method_info['method'], class_node)
                if len(caller_node.body) == 0:
                    void_callers.append(caller)
                else:
                    caller_info['fitness'] = random()
        self.code_modifier.delete_method(class_node, method_info['method'])
        self.reference_graph.remove_node(method)
        if len(class_node.body) == 0:
            self.inheritance_graph.remove_node(class_node.name)
        # recursively remove all void callers
        for caller in void_callers:
            self.delete_method(caller)

    def create_class(self):
        superclass_name = None
        if random() > self.p_no_inherit:
            class_names = []
            num_subclasses = []
            for node, in_degree in self.inheritance_graph.in_degree_iter():
                class_names.append(node)
                num_subclasses.append(in_degree)

            superclass_name = sample(class_names, [n + 1 for n in num_subclasses])
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

