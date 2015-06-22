from networkx import DiGraph, Graph
import logging
import simpy
from random import random, gauss, seed
from math import floor, exp
from time import time

from plyj.model import MethodDeclaration, MethodInvocation
from codevo.utils import sample
from codevo.codebase import Codebase


class Evolver:
    def __init__(self):
        self._env = simpy.Environment()
        manager = Manager(self._env)
        self.codebase = Codebase()
        for i in range(5):
            Developer(self._env, manager, self.codebase)

    def step(self):
        p_create_method = 12
        p_call_method = 17
        p_delete_method = 1
        p_update_method = 88
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
        method = self.codebase.create_method(klass)
        # make a call from the new method
        self.call_method(method.name)
        # call the new method
        caller_name = self.choose_unfit_method()
        self.call_method(caller_name, method.name)
        return 3

    def call_method(self, caller_name=None, callee_name=None):
        logging.info('calling a method')
        caller_info = self.reference_graph.node[caller_name] if caller_name \
            else sample([(data, len(data['method'].body)) for data in self.reference_graph.node.values()])
        callee_info = self.reference_graph.node[callee_name or self.choose_callee()]
        return 1

    def update_method(self):
        logging.info('updating a method')
        method_name = self.choose_unfit_method()
        method_info = self.reference_graph.node[method_name]
        # The method can be empty because it is the only remaining method
        if len(method_info['method'].body) == 0 or random() < 0.67:
            self.codebase.add_statement(method_info['method'])
        else:
            deleted_stmt = self.codebase.delete_statement(method_info['method'])
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
                self.codebase.delete_method_call(caller, method_info['method'], klass)
                change_size += 1
                if len(caller.body) == 0:
                    void_callers.append(caller_name)
                else:
                    caller_info['fitness'] = random()

        self.codebase.delete_method(klass, method_info['method'])
        change_size += len(method_info['method'].body)
        self.reference_graph.remove_node(method_name)
        change_size += 1
        # recursively remove all empty callers
        for caller_name in void_callers:
            change_size += self.delete_method(caller_name)
        if len(klass.body) == 0:
            # remove the class and all its subclasses
            # cannot use predecessors_iter because the elements will be removed from the graph
            for class_name in self.inheritance_graph.predecessors(klass.name):
                c = self.inheritance_graph.node[class_name]['class']
                method_names = []
                for member in c.body:
                    if isinstance(member, MethodDeclaration):
                        method_names.append(member.name)
                for m in method_names:
                    change_size += self.delete_method(m)
                # do not need to remove the subclass from the graph because it was
                # removed after its last method was deleted
            self.inheritance_graph.remove_node(klass.name)
            change_size += 1
        return change_size

    def create_class(self):
        superclass_name = None
        if random() > self.p_no_inherit:
            class_info = [(node, in_degree + 1) for node, in_degree in self.inheritance_graph.in_degree_iter()]
            superclass_name = sample(class_info)
        klass = self.codebase.create_class(superclass_name)
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



class Developer:
    def __init__(self, env, manager, codebase):
        self._env = env
        self._manager = manager
        self._memory = []
        self._codebase = codebase
        self._p_grow_method = 0.5
        self._p_create_method = 0.3
        self._p_create_class = 0.1
        self._p_has_super = 0.5
        # refactorings
        self._p_rename = 0.4
        self._p_move = 0.5

        env.process(self.work())

    def work(self):
        # TODO acquire locks
        while True:
            if self._manager.has_more_tasks():
                # developing new features
                self._manager.assign_task()
                method_name = self._codebase.choose_random_method()
                for i in range(10):
                    # inspect the method
                    yield self._env.timeout(self.get_reading_time(method_name))
                    if not self._codebase.has_method(method_name):
                        # The method may be deleted or rename during reading time
                        method_name = self._codebase.choose_random_method()
                        continue
                    if random() < self._p_grow_method:
                        self._codebase.add_statement(method_name)
                    else:
                        # make a method call
                        self._memory = [m for m in self._memory if self._codebase.has_method(m)]
                        if random() < self._p_create_method:
                            # create a new method
                            if random() < self._p_create_class:
                                # create a new class for the method
                                superclass_name = None
                                if random() < self._p_has_super:
                                    # has a super class
                                    memory_size = len(self._memory)
                                    if memory_size > 0:
                                        superclass_name = [self._codebase.get_class_name(m)
                                                           for m in self._memory][floor(random() * memory_size)]
                                class_name = self._codebase.create_class(superclass_name).name
                            else:
                                # choose from an existing class
                                class_name = self._codebase.choose_random_class()
                            callee_name = self._codebase.create_method(class_name).name
                            self._memory.append(callee_name)
                        else:
                            # call an existing method
                            memory_size = len(self._memory)
                            if memory_size > 0:
                                callee_name = self._memory[floor(random() * memory_size)]
                            else:
                                callee_name = self._codebase.choose_random_method()
                        self._codebase.add_method_call(method_name, callee_name)
                    self._memory.append(method_name)
                    # walk to a neighbor
                    method_name = self._codebase.choose_random_neighbor(method_name)
                    if method_name is None:
                        method_name = self._codebase.choose_random_method()
            else:
                # refactoring
                n = random()
                if self._codebase.number_of_methods() == 1 or n < self._p_rename:
                    unfit_method_name = self._codebase.least_fit_methods()[0]
                    yield self._env.timeout(self.get_reading_time(unfit_method_name))
                    # rename a method, don't need to understand callers
                    if not self._codebase.has_method(unfit_method_name):
                        continue
                    new_method_name = self._codebase.rename_method(unfit_method_name)
                    self._memory = [new_method_name if m == unfit_method_name else m for m in self._memory]
                    self._memory.append(new_method_name)
                elif self._codebase.number_of_classes() == 1 or n > self._p_rename + self._p_move:
                    # merge two methods
                    delete_method_name, update_method_name = self._codebase.least_fit_methods(2)
                    # Understanding the relevant methods
                    reading_time = self.get_reading_time(delete_method_name) + self.get_reading_time(update_method_name)
                    for method_name in self._codebase.caller_names(delete_method_name):
                        reading_time += self.get_reading_time(method_name)
                    for method_name in self._codebase.caller_names(update_method_name):
                        reading_time += self.get_reading_time(method_name)
                    yield self._env.timeout(reading_time)
                    # Examine if the methods still exist
                    if not self._codebase.has_method(delete_method_name) or \
                            not self._codebase.has_method(update_method_name):
                        continue
                    # Delete the method
                    caller_names = [n for n in self._codebase.caller_names(delete_method_name)
                                    if n != delete_method_name]
                    self._codebase.delete_method(delete_method_name)
                    self._memory = [m for m in self._memory if m != delete_method_name]
                    # Add a parameter to another method
                    self._codebase.add_parameter(update_method_name)
                    self._memory.append(update_method_name)
                    for method_name in self._codebase.caller_names(update_method_name):
                        self._memory.append(method_name)
                    # Make the callers of the former method call the latter method
                    for method_name in caller_names:
                        self._codebase.add_method_call(method_name, update_method_name)
                        self._memory.append(method_name)
                else:
                    unfit_method_name = self._codebase.least_fit_methods()[0]
                    yield self._env.timeout(self.get_reading_time(unfit_method_name))
                    # move a method closer to its callers, don't need to understand callers
                    if not self._codebase.has_method(unfit_method_name):
                        continue
                    class_name = self._codebase.get_class_name(unfit_method_name)
                    # initialize the original class name to 0.5 to break tie
                    reference_counts = {class_name: 0.5}
                    for method_name in self._codebase.caller_names(unfit_method_name):
                        class_name = self._codebase.get_class_name(method_name)
                        if class_name in reference_counts:
                            reference_counts[class_name] += 1
                        else:
                            reference_counts[class_name] = 1
                    closest_class_name = max(reference_counts, key=lambda c: reference_counts[c])
                    self._codebase.move_method(unfit_method_name, closest_class_name)
                    self._memory.append(unfit_method_name)

    def get_reading_time(self, method_name):
        """
        Calculate the time to understand a method
        :param method_name:
        :return:
        """
        reading_time = self._codebase.size_of(method_name)
        if method_name in self._memory:
            # Forgetting curve: https://en.wikipedia.org/wiki/Forgetting_curve
            reading_time *= 1 - exp(-self._memory.index(method_name)/40)
        return reading_time + 1


class Manager:
    def __init__(self, env):
        self.env = env
        self.tasks = 0
        env.process(self.work())

    def has_more_tasks(self):
        return self.tasks > 0

    def assign_task(self):
        self.tasks -= 1
        logging.info('Task queue size: %d' % self.tasks)

    def work(self):
        while True:
            self.tasks += 1
            logging.info('Task queue size: %d' % self.tasks)
            yield self.env.timeout(20)

if __name__ == '__main__':
    random_seed = round(time())
    print('Using seed', random_seed)
    seed(random_seed)
    logging.basicConfig(level=logging.INFO)
    env = simpy.Environment()
    m = Manager(env)
    codebase = Codebase()
    d1 = Developer(env, m, codebase)
    d2 = Developer(env, m, codebase)
    env.run(until=2000)
    codebase.save()