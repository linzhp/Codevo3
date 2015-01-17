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
        self.p_create_method = 0.1
        self.p_call_method = 0.9
        self.p_change_method = 0.9
        self.p_delete_method = 0.1
        self.p_create_class = 0.1
        self.p_no_inherit = 0.1
        self.code_modifier = CodeModifier()
        self.inheritance_graph = DiGraph()
        self.reference_graph = DiGraph()

        for c in initial_classes:
            self.inheritance_graph.add_node(c.name, {'class': c})
            for m in c.body:
                if isinstance(m, MethodDeclaration):
                    self.reference_graph.add_node(m.name, {'method': m, 'class': c, 'fitness': random()})

    def step(self):
        action = sample([self.create_method, self.call_method, self.change_method, self.delete_method],
               [self.p_create_method, self.p_call_method, self.p_change_method, self.p_delete_method])
        action()

    def create_method(self):
        klass = None
        if random() < self.p_create_class:
            klass = self.create_class()
        else:
            classes = []
            sizes = []
            for node, data in self.inheritance_graph.nodes_iter(data=True):
                classes.append(data['class'])
                sizes.append(len(data['class'].body))
            klass = sample(classes, sizes)
        method = self.code_modifier.create_method(klass)
        self.reference_graph.add_node(method.name, {'method': method, 'class': klass, 'fitness': random()})
        return method

    def call_method(self):
        methods = []
        sizes = []
        in_degrees = []
        for node, in_degree in self.reference_graph.in_degree_iter():
            in_degrees.append(in_degree)
            data = self.reference_graph.node[node]
            methods.append(data)
            sizes.append(len(data['method'].body))

        caller_info = sample(methods, sizes)
        callee_info = sample(methods, in_degrees)
        self.code_modifier.create_reference(
            caller_info['method'], callee_info['method'], callee_info['class'])
        # does this make the system too unstable?
        caller_info['fitness'] = random()
        self.reference_graph.add_edge(caller_info['method'].name, callee_info['method'].name)

    def change_method(self):
        method = self.choose_unfit_method()


    def delete_method(self):
        pass

    def create_class(self):
        superclass_name = None
        if random() > self.p_no_inherit:
            class_names = []
            num_subclasses = []
            for node, in_degree in self.inheritance_graph.in_degree_iter():
                class_names.append(node)
                num_subclasses.append(in_degree)

            superclass_name = sample(class_names, num_subclasses)
        klass = self.code_modifier.create_class(superclass_name)
        self.inheritance_graph.add_node(klass.name, {'class': klass})
        if superclass_name:
            self.inheritance_graph.add_edge(klass.name, superclass_name)
        return klass

    def choose_unfit_method(self):
        """
        :return: the method with least fitness number. Can change to a probabilistic function that biases towards
        less fit methods
        """
        min_fitness = 1
        unfit_method = None
        for method, data in self.reference_graph.nodes_iter(True):
            if data['fitness'] < min_fitness:
                min_fitness = data['fitness']
                unfit_method = method
        return unfit_method

