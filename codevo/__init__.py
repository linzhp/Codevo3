from plyj.model import *
from plyj.parser import Parser
from random import random
from codevo.utils import sample
from os import path
from networkx import DiGraph


class CodeModifier:
    def __init__(self):
        self.counter = 0

    def create_method(self, class_node):
        """
        The created methods are static methods for now
        """
        method = MethodDeclaration(
            'method' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        class_node.body.append(method)
        return method

    def delete_method(self, class_node, method):
        class_node.body.remove(method)

    def create_class(self, superclass_name):
        klass = ClassDeclaration('Class' + str(self.counter), [])
        if superclass_name:
            klass.extends = Type(Name(superclass_name))
        self.counter += 1
        return klass

    def create_reference(self, from_method, to_method, target):
        ref = MethodInvocation(to_method, target=target)
        from_method.body.append(ref)
        return ref

    def delete_reference(self, from_method, to_method, target):
        to_delete = []
        for stmt in from_method.body:
            if isinstance(stmt, MethodInvocation) and \
                    stmt.name == to_method.name:
                to_delete.append(stmt)

        for stmt in to_delete:
            from_method.body.remove(stmt)


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
        self.a1 = 0.3
        self.a2 = 0.3
        self.a3 = 0.3
        self.code_modifier = CodeModifier()
        self.inheritance_graph = DiGraph()
        self.reference_graph = DiGraph()

        for c in initial_classes:
            self.inheritance_graph.add_node(c.name, {'class': c})
            for m in c.body:
                if isinstance(m, MethodDeclaration):
                    self.reference_graph.add_node(m.name, {'method': m, 'class': c})

    def step(self):
        if random() < self.a1:
            self.create_method()
        else:
            self.call_method()

    def create_method(self):
        klass = None
        if random() < self.a2:
            klass = self.create_class()
        else:
            classes = []
            sizes = []
            for node, data in self.inheritance_graph.nodes_iter(data=True):
                classes.append(data['class'])
                sizes.append(len(data['class'].body))
            klass = sample(classes, sizes)
        method = self.code_modifier.create_method(klass)
        self.reference_graph.add_node(method.name, {'method': method, 'class': klass})
        return method

    def call_method(self):
        methods = []
        sizes = []
        in_degrees = []
        for node, data in self.reference_graph.nodes_iter(True):
            methods.append(data)
            sizes.append(len(data['method'].body))
            in_degrees.append(self.reference_graph.in_degree(node))
        caller_info = sample(methods, sizes)
        callee_info = sample(methods, in_degrees)
        caller_info['method'].body.append(
            MethodInvocation(callee_info['method'].name, target=Name(callee_info['class'].name)))
        self.reference_graph.add_edge(caller_info['method'].name, callee_info['method'].name)

    def create_class(self):
        superclass_name = None
        if random() > self.a3:
            class_names = []
            num_subclasses = []
            for node in self.inheritance_graph.nodes_iter():
                class_names.append(node)
                num_subclasses.append(self.inheritance_graph.in_degree(node))
            superclass_name = sample(class_names, num_subclasses)
        klass = self.code_modifier.create_class(superclass_name)
        self.inheritance_graph.add_node(klass.name, {'class': klass})
        if superclass_name:
            self.inheritance_graph.add_edge(klass.name, superclass_name)
        return klass