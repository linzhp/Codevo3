from plyj.model import *
from random import random
from codevo.utils import sample

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
    def __init__(self, classes):
        self.a1 = 0.3
        self.a2 = 0.3
        self.code_modifier = CodeModifier()
        self.classes = classes
        self.methods = {}
        self.callers = {}

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
            klass = sample(self.classes, [len(c.body) for c in self.classes])
        method = self.code_modifier.create_method(klass)
        self.methods[method.name] = (method, klass)
        self.callers[method.name] = []
        return method

    def call_method(self):
        method_names = self.methods.keys()
        caller_name = sample(method_names, [len(self.methods[m][0].body) for m in method_names])
        caller = self.methods[caller_name][0]
        callee_name = sample(method_names, [len(self.callers[m]) for m in self.callers])
        target = self.methods[callee_name][1]
        caller.body.append(MethodInvocation(callee_name, target=Name(target.name)))
        self.callers[callee_name].append(caller_name)

    def create_class(self):
        pass