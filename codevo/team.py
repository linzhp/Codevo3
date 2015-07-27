import logging
from random import random, lognormvariate
from math import floor, exp, ceil

class Developer:
    def __init__(self, manager):
        self._env = manager.env
        self._manager = manager
        self._memory = []
        self._codebase = manager.codebase
        self._p_grow_method = 0.5
        self._p_create_method = 0.2
        self._p_create_class = 0.1
        self._p_has_super = 0.5
        # refactorings
        self._p_rename = 0.4
        self._p_move = 0.5

        self._env.process(self.work())

    def work(self):
        while True:
            change_size = 0
            if self._manager.has_more_tasks():
                # developing new features
                task_size = self._manager.assign_task()
                method_name = self._codebase.choose_random_method()
                for i in range(task_size):
                    # inspect the method
                    yield self._env.timeout(self.get_reading_time(method_name))
                    if not self._codebase.has_method(method_name):
                        # The method may be deleted or rename during reading time
                        method_name = self._codebase.choose_random_method()
                        continue
                    if random() < self._p_grow_method:
                        change_size += self._codebase.add_statement(method_name)
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
                                c, class_name = self._codebase.create_class(superclass_name)
                                change_size += c
                            else:
                                # choose from an existing class
                                class_name = self._codebase.choose_random_class()
                            c, callee_name = self._codebase.create_method(class_name)
                            change_size += c
                            self._memory.append(callee_name)
                        else:
                            # call an existing method
                            memory_size = len(self._memory)
                            if memory_size > 0:
                                callee_name = self._memory[floor(random() * memory_size)]
                            else:
                                callee_name = self._codebase.choose_random_method()
                            # if random() > 0.5:
                            #     # Evolve the existing method
                            #     change_size += self._codebase.add_parameter(callee_name)
                        change_size += self._codebase.add_method_call(method_name, callee_name)
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
                    c, new_method_name = self._codebase.rename_method(unfit_method_name)
                    change_size += c
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
                    change_size += self._codebase.delete_method(delete_method_name)
                    self._memory = [m for m in self._memory if m != delete_method_name]
                    # Add a parameter to another method
                    change_size += self._codebase.add_parameter(update_method_name)
                    self._memory.append(update_method_name)
                    for method_name in self._codebase.caller_names(update_method_name):
                        self._memory.append(method_name)
                    # Make the callers of the former method call the latter method
                    for method_name in caller_names:
                        # treat them as updating method calls, so the change size doesn't increase here
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
                    change_size += self._codebase.move_method(unfit_method_name, closest_class_name)
                    self._memory.append(unfit_method_name)
            if change_size > 0:
                self._codebase.commit(change_size)

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
    def __init__(self, env, codebase):
        self.env = env
        self.tasks = 0
        self.codebase = codebase
        env.process(self.work())
        self.developers = [Developer(self)]

    def has_more_tasks(self):
        return self.tasks > 0

    def assign_task(self):
        self.tasks -= 1
        logging.info('Task assigned, queue size: %d' % self.tasks)
        return ceil(lognormvariate(2, 1))

    def work(self):
        while True:
            if self.tasks < 10:
                # thinking out new task
                logging.info('%d: Creating new task...' % self.env.now)
                yield self.env.timeout(20)
                self.tasks += 1
                logging.info('Task created, queue size: %d' % self.tasks)
            else:
                # recruiting new developer
                logging.info('%d: Recruiting new developer' % self.env.now)
                yield self.env.timeout(20)
                self.developers.append(Developer(self))
                logging.info('Developer joined, team size: %d' % len(self.developers))
