from os import path
from random import random
from networkx import DiGraph, relabel_nodes
from math import floor

from plyj.model import *
from plyj.parser import Parser

from codevo.utils import sample
from codevo.java_printer import JavaPrinter


class Codebase:
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

    def size_of(self, method_name):
        return len(self.reference_graph.node[method_name]['method'].body)

    def number_of_methods(self):
        return len(self.reference_graph)

    def number_of_classes(self):
        return len(self.inheritance_graph)

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

    def choose_least_fit(self):
        """
        :return: the name of the method with the least fitness value
        """
        return min(self.reference_graph, key=lambda n: self.reference_graph.node[n]['fitness'])

    def choose_random_neighbor(self, method_name):
        neighbors = self.reference_graph.neighbors(method_name)
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
        return self.reference_graph.predecessors_iter(method_name)

    def create_method(self, class_name):
        """
        The created methods are static methods for now
        """
        klass = self.inheritance_graph.node[class_name]['class']
        method = MethodDeclaration(
            'method' + str(self.counter),
            body=[], modifiers=['static'])
        self.counter += 1
        klass.body.append(method)
        method_info = {'method': method, 'class_name': class_name, 'fitness': random()}
        self.reference_graph.add_node(method.name, method_info)
        return method

    def delete_method(self, method_name):
        """
        Delete the method and update callers
        :param method_name:
        :return:
        """
        # remove method invocation
        for caller_name in self.reference_graph.predecessors_iter(method_name):
            caller_info = self.reference_graph.node[caller_name]
            caller = caller_info['method']
            caller.body = [stmt for stmt in caller.body
                           if not Codebase.is_invocation(stmt, method_name)
                           ]
            caller_info['fitness'] = random()
        method_info = self.reference_graph.node[method_name]
        method = method_info['method']
        class_name = method_info['class_name']
        klass = self.inheritance_graph.node[class_name]['class']
        klass.body.remove(method)
        self.reference_graph.remove_node(method_name)
        if len(klass.body) == 0:
            # remove inheritance from all subclasses
            for subclass_name in self.inheritance_graph.predecessors_iter(class_name):
                subclass = self.inheritance_graph.node[subclass_name]['class']
                subclass.extends = None
            self.inheritance_graph.remove_node(class_name)

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
        callee_info = self.reference_graph.node[callee_name]
        caller_info = self.reference_graph.node[caller_name]
        caller = caller_info['method']
        num_params = len(callee_info['method'].parameters)
        # trying to find enough variables for the method arguments
        arguments = [Name(p.variable.name) for p in caller.parameters]
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
        self.reference_graph.add_edge(caller_name, callee_name)
        caller_info['fitness'] = random()
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
        method_info = self.reference_graph.node[method_name]
        method = method_info['method']
        stmt = self.create_variable_declaration()
        method.body.append(stmt)
        method_info['fitness'] = random()

    def add_parameter(self, method_name):
        """
        Add a parameter to the method, and update all its callers
        :param method_name:
        :return:
        """
        method_info = self.reference_graph.node[method_name]
        method = method_info['method']
        parameters = method.parameters
        parameters.append(FormalParameter(Variable('param%d' % len(parameters)), Type(Name('int'))))
        for caller_name in self.reference_graph.predecessors_iter(method_name):
            caller_info = self.reference_graph.node[caller_name]
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
            caller_info['fitness'] = random()

    def move_method(self, method_name, to_class_name):
        method_info = self.reference_graph.node[method_name]
        from_class_name = method_info['class_name']
        if from_class_name == to_class_name:
            return
        method = method_info['method']
        from_class_body = self.inheritance_graph.node[from_class_name]['class'].body
        from_class_body.remove(method)
        to_class_body = self.inheritance_graph.node[to_class_name]['class'].body
        to_class_body.append(method)
        method_info['class_name'] = to_class_name
        # update references
        for method_invocation in self.method_invocations(method_name):
            method_invocation.target = Name(to_class_name)

    def rename_method(self, method_name):
        new_name = 'method%d' % self.counter
        self.counter += 1
        method_info = self.reference_graph.node[method_name]
        method_info['method'].name = new_name
        for inv in self.method_invocations(method_name):
            inv.name = new_name
        relabel_nodes(self.reference_graph, {method_name: new_name}, copy=False)
        method_info['fitness'] = random()
        return new_name

    def method_invocations(self, method_name):
        """
        Generator for MethodInvocation instances of method_name
        :param method_name:
        :return:
        """
        for caller_name in self.reference_graph.predecessors_iter(method_name):
            caller = self.reference_graph.node[caller_name]['method']
            for stmt in caller.body:
                if Codebase.is_invocation(stmt, method_name):
                    yield stmt.expression

    @staticmethod
    def is_invocation(stmt, method_name):
        return isinstance(stmt, ExpressionStatement) and \
               isinstance(stmt.expression, MethodInvocation) and \
               stmt.expression.name == method_name

    def delete_statement(self, method):
        return method.body.pop()

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

    def save(self):
        for class_name, data in self.inheritance_graph.nodes_iter(True):
            klass = data['class']
            java_printer = JavaPrinter()
            klass.accept(java_printer)
            with open(path.join('output/src', class_name + '.java'), 'w') as java_file:
                java_file.write(java_printer.result)
