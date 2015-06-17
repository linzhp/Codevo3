from os import path
from random import random
from networkx import DiGraph
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
        return min(self.reference_graph, lambda n: self.reference_graph[n]['fitness'])

    def choose_random_neighbor(self, method_name):
        neighbors = self.reference_graph.neighbors(method_name)
        num_neighbors = len(neighbors)
        if num_neighbors > 0:
            return neighbors[floor(random() * num_neighbors)]
        else:
            return None

    def get_callers(self, method_name):
        """
        :param method_name:
        :return: caller method names
        """
        return self.reference_graph.predecessors(method_name)

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
        Delete the method without updating callers
        :param method_name:
        :return:
        """
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
        num_params = len(callee_info['method'].paramenters)
        # trying to find enough variables for the method arguments
        arguments = [Name(p.variable.name) for p in caller.parameters]
        for s in caller.body:
            if len(arguments) >= num_params:
                break
            if isinstance(s, VariableDeclaration):
                arguments.append(s.variable.name)
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
        for caller_name, data in self.reference_graph.predecessors_iter(method_name):
            caller = data['method']
            local_variables = [p.variable.name for p in caller.parameters]
            for s in caller.body:
                if isinstance(s, VariableDeclaration):
                    local_variables.append(s.variable.name)
                elif isinstance(s, ExpressionStatement) and \
                    isinstance(s.expression, MethodInvocation) and \
                    s.expression.name == method_name:
                    if len(local_variables) > 0:
                        s.expression.arguments.append(Name(local_variables[-1]))
                    else:
                        s.expression.arguments.append(Literal(self.counter))
            data['fitness'] = random()

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