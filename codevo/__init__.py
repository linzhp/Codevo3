from plyj.model import *
from random import random

class CodeModifier:
    def __init__(self):
        self.counter = 0

    def create_method(self, class_node):
        """
        The created methods are static methods for now
        """
        method = MethodDeclaration(
            'method_' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        class_node.body.append(method)
        return method

    def delete_method(self, class_node, method):
        class_node.body.remove(method)

    def create_class(self):
        klass = ClassDeclaration('Class' + str(self.counter))
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
    def __init__(self):
        self.a1 = 0.3
        self.a2 = 0.3
        self.code_modifier = CodeModifier()

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
            pass

    def call_method(self):
        pass

    def create_class(self):
        pass